import logging
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import List

import napkon_string_matching.types.comparable as comp
import numpy as np
import pandas as pd
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    ITEM = "Item"
    SHEET = "Sheet"
    FILE = "File"
    HEADER = "Header"
    QUESTION = "Question"
    OPTIONS = "Options"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"


DATASETTABLE_COLUMN_DB_COLUMN = "Datenbankspalte"
DATASETTABLE_COLUMN_FILE = "FileName"
DATASETTABLE_COLUMN_ITEM = "Item"
DATASETTABLE_COLUMN_OPTIONS = "Optionen (durch Semikolons getrennt), Lookuptabelle"
DATASETTABLE_COLUMN_PROJECT = "Projekt"
DATASETTABLE_COLUMN_QUESTION = "Frage"
DATASETTABLE_COLUMN_NUMBER = "Nr."
DATASETTABLE_COLUMN_SHEET_NAME = "SheetName"
DATASETTABLE_COLUMN_TYPE = "Fragetyp (Konfiguration)"
DATASETTABLE_COLUMN_VARIABLE = "Datenbankspalte"

DATASETTABLE_TYPE_GROUP_DEFAULT = "StandardGroup"
DATASETTABLE_TYPE_GROUP_HORIZONAL = "HorizontalGroup"
DATASETTABLE_TYPE_HEADER = "Headline"

COLUMN_TEMP_SUBHEADER = "Subheader"

DATASETTABLE_ITEM_SKIPABLE = "<->"


logger = logging.getLogger(__name__)


class QuestionnaireBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.SHEET.value


class QuestionnaireCategory(QuestionnaireBase, Category):
    pass


class Questionnaire(QuestionnaireBase, ComparableData):
    __column_mapping__ = {Columns.PARAMETER.value: comp.Columns.PARAMETER.value}
    __category_type__ = QuestionnaireCategory

    def concat(self, others: List):
        if len(others) == 0:
            return self

        if not isinstance(others[0], Questionnaire):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(others[0]).__name__
                )
            )

        return Questionnaire(
            pd.concat([self._data, *[other._data for other in others]], ignore_index=True)
        )

    @staticmethod
    def read_original_format(file_name, *args, **kwargs):
        return Questionnaire.read_dataset_table(file_name, *args, **kwargs)

    @staticmethod
    def read_dataset_table(file: str | Path, *args, **kwargs):
        """
        Read a xlsx file

        The contents are returned as a list of dictionaries containing the row contents
        and meta information.

        attr
        ---
            xlsx_file (str|Path): file to read

        returns
        ---
            Questionnaire: parsed result
        """

        logger.info("read from file %s...", str(file))

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            file = pd.ExcelFile(file, engine="openpyxl")
        sheet_names = file.sheet_names[2:]

        logger.info("...reading %i sheets...", len(sheet_names))

        parser = SheetParser()
        sheets = []
        for sheet_name in sheet_names:
            data_list = parser.parse(file, sheet_name, *args, **kwargs)
            if data_list is not None:
                sheets.append(data_list)

        if not sheets:
            logger.warn("...dit not get any entries")
            return None

        result = Questionnaire().concat(sheets)

        logger.info("...got %i entries", len(result))

        return result

    def add_terms(self, language: str = "german"):
        logger.info("add terms...")
        result = [
            Questionnaire.gen_term(header, question, item, language=language)
            for header, question, item in zip(self.header, self.question, self.item)
        ]
        self.term = result
        logger.info("...done")

    @staticmethod
    def gen_term(categories: List[str], question: str, item: str, language: str = "german") -> str:
        term_parts = get_term_parts(categories, question, item)
        return ComparableData.gen_term(term_parts, language)


def get_term_parts(categories: List[str], question: str, item: str) -> List[str]:
    term_parts = []

    if categories:
        term_parts += categories
    if question:
        term_parts.append(question)
    if item:
        term_parts.append(item)

    return term_parts


class SheetParser:
    """
    A parser for sheets of a dataset table
    """

    def __init__(self) -> None:
        self.current_categories = []
        self.current_question = None

    def parse(
        self,
        file: pd.ExcelFile,
        sheet_name: str,
        *args,
        **kwargs,
    ) -> Questionnaire:
        """
        Parses a single sheet

        Extracts meta information and information needed for matching
        and returns them as a list

        attr
        ---
            file (Excelfile): opened excel file
            sheet_name (str): name of the sheet to parse

        returns
        ---
            List[dict]: list of dictionary per line
        """
        self.current_categories = []
        self.current_question = None

        sheet: pd.DataFrame = pd.read_excel(
            file, sheet_name=sheet_name, na_values=DATASETTABLE_ITEM_SKIPABLE
        )

        # Remove leading meta information block on sheet
        start_index = np.where(sheet[DATASETTABLE_COLUMN_PROJECT] == DATASETTABLE_COLUMN_NUMBER)[0][
            0
        ]
        sheet.columns = sheet.iloc[start_index]
        sheet = sheet.iloc[start_index + 1 :, :].reset_index(drop=True)

        # Replace `NaN` with `None` for easier handling
        sheet.where(pd.notnull(sheet), None, inplace=True)

        # Add meta information to each row
        sheet_name = re.sub(r"[\.\(\),]", "", sheet_name.strip(" .-"))
        sheet_name = re.sub(r"[ \-]+", "_", sheet_name).replace("__", "_")
        sheet[DATASETTABLE_COLUMN_SHEET_NAME] = sheet_name
        sheet[DATASETTABLE_COLUMN_FILE] = Path(file.io).stem

        return self.parse_rows(sheet, *args, **kwargs)

    def parse_rows(
        self,
        sheet: pd.DataFrame,
        filter_column: str = None,
        filter_prefix: str = None,
        *args,
        **kwargs,
    ) -> Questionnaire | None:

        # Fill category and subcategory if available
        sheet[Columns.HEADER.value] = [
            question if type_ == DATASETTABLE_TYPE_HEADER else None
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
        ]
        sheet[COLUMN_TEMP_SUBHEADER] = [
            question
            if pd.notna(type_)
            and type_ != DATASETTABLE_TYPE_HEADER
            and all(entry not in type_ for entry in ["Group", "Matrix"])
            else None
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
        ]

        # Fill for all items category and subcategory if they belong to one
        sheet[Columns.HEADER.value] = sheet[Columns.HEADER.value].ffill()
        sheet[COLUMN_TEMP_SUBHEADER] = _fill_subcategories(
            sheet[Columns.HEADER.value], sheet[COLUMN_TEMP_SUBHEADER]
        )

        # Combine both information in a single column
        sheet[Columns.HEADER.value] = [
            _combine_headers(category, sub)
            for category, sub in zip(sheet[Columns.HEADER.value], sheet[COLUMN_TEMP_SUBHEADER])
        ]
        sheet.drop(columns=COLUMN_TEMP_SUBHEADER, inplace=True)

        # Remove all entries without items and variable names
        sheet.dropna(subset=[DATASETTABLE_COLUMN_ITEM, DATASETTABLE_COLUMN_DB_COLUMN], inplace=True)

        # Fill down questions to sub-items
        sheet[DATASETTABLE_COLUMN_QUESTION] = sheet[DATASETTABLE_COLUMN_QUESTION].ffill()

        # Filter entries if filter provided
        if filter_column and filter_prefix:
            sheet.drop(
                sheet[
                    [
                        not entry.startswith(filter_prefix) if pd.notna(entry) else False
                        for entry in sheet[filter_column]
                    ]
                ].index,
                inplace=True,
            )

        # Rename columns
        mappings = {
            DATASETTABLE_COLUMN_ITEM: Columns.ITEM.value,
            DATASETTABLE_COLUMN_SHEET_NAME: Columns.SHEET.value,
            DATASETTABLE_COLUMN_FILE: Columns.FILE.value,
            DATASETTABLE_COLUMN_QUESTION: Columns.QUESTION.value,
            DATASETTABLE_COLUMN_VARIABLE: Columns.VARIABLE.value,
        }
        sheet.rename(columns=mappings, inplace=True)
        result = Questionnaire(sheet)

        # Re-build variables using the sheet name to make them unique
        result.variable = [
            f"{sheet}-{variable}" for sheet, variable in zip(result.sheet, result.variable)
        ]

        # Create identifier column
        result.identifier = [
            _generate_identifier(file, sheet, str(index))
            for file, sheet, index in zip(result.file, result.sheet, result.index)
        ]

        # Set options
        options = result.get(DATASETTABLE_COLUMN_OPTIONS)
        result.options = (
            [_generate_options(options_) for options_ in options] if options is not None else None
        )

        # Generate parameter
        result.parameter = [
            ":".join(get_term_parts(header, question, item))
            for header, question, item in zip(result.header, result.question, result.item)
        ]

        result.drop_superfluous_columns()

        return result


def _fill_subcategories(categories: pd.Series, subcategories: pd.Series) -> List:
    result = []
    for index, entry in enumerate(zip(categories, subcategories)):
        prev_cat = categories[index - 1] if index > 0 else -1
        prev_sub = result[index - 1] if index > 0 else -1
        cat, sub = entry

        if not sub and prev_sub and prev_cat == cat:
            result.append(prev_sub)
        else:
            result.append(sub)
    return result


def _generate_identifier(file: str, sheet: str, row_name: str) -> str:
    return "#".join([file, sheet, row_name]).replace(" ", "-")


def _generate_options(options: str) -> List[str] | None:
    return (
        options.replace(";", "\n").replace("\n\n", "\n").splitlines() if pd.notna(options) else None
    )


def _combine_headers(first: str, second: str) -> List[str]:
    result = []
    if pd.notna(first):
        result.append(first)
    if pd.notna(second):
        result.append(second)
    return result if result else None
