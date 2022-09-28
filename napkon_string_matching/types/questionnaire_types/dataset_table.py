import logging
import re
import warnings
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from napkon_string_matching.types.dataset_definition import DatasetDefinition
from napkon_string_matching.types.identifier import generate_id
from napkon_string_matching.types.questionnaire import Columns, Questionnaire, get_term_parts

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

DATASETTABLE_SHEET_HIDDEN_TAG = "Ausgeblendet"
DATASETTABLE_SHEET_HIDDEN_TRUE = "ja"
DATASETTABLE_SHEET_TABLES_TAG = "Tabelle(n)"
DATASETTABLE_SHEET_TABLES_MAIN_PREFIX = "mnp"

COLUMN_TEMP_SUBHEADER = "Temp_Subheader"
COLUMN_TEMP_TABLE = "Temp_Table"

DATASETTABLE_ITEM_SKIPABLE = "<->"

logger = logging.getLogger(__name__)


class DatasetTable(Questionnaire):
    def __init__(
        self,
        data=None,
        subgroup_names: Dict[str, str] = None,
        subgroups: Dict[str, List[str]] = None,
    ):
        super().__init__(data)
        self.subgroup_names = subgroup_names if subgroup_names else {}
        self.subgroups = subgroups if subgroups else {}

    @staticmethod
    def read_original_format(file_name: str | Path, *args, **kwargs):
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

        logger.info("read from file %s...", str(file_name))

        file: pd.ExcelFile = None
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            file = pd.ExcelFile(file_name, engine="openpyxl")
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

        result = DatasetTable().concat(sheets)

        logger.info("...got %i entries", len(result))

        return result

    def concat(self, others: List):
        result = super().concat(others)
        result.subgroup_names = {k: v for d in others for k, v in d.subgroup_names.items()}
        result.subgroups = {k: v for d in others for k, v in d.subgroups.items()}
        return result


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
    ) -> DatasetTable | None:
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

        # Do not process hidden sheets
        hidden = _get_meta(sheet, DATASETTABLE_SHEET_HIDDEN_TAG)
        if hidden and hidden.lower() == DATASETTABLE_SHEET_HIDDEN_TRUE:
            return None

        table_names = _get_meta(sheet, DATASETTABLE_SHEET_TABLES_TAG)
        if table_names:
            table_names = table_names.replace(" ", "").split(",")

        # Remove leading meta information block on sheet
        start_index = np.where(sheet[DATASETTABLE_COLUMN_PROJECT] == DATASETTABLE_COLUMN_NUMBER)[0][
            0
        ]
        sheet.columns = sheet.iloc[start_index]
        sheet = sheet.iloc[start_index + 1 :, :].reset_index(drop=True)

        # Replace `NaN` with `None` for easier handling
        sheet.where(pd.notnull(sheet), None, inplace=True)

        # Add meta information to each row
        sheet_name = re.sub(r"[ \-\.\(\),]+", "_", sheet_name)
        sheet[DATASETTABLE_COLUMN_SHEET_NAME] = sheet_name
        sheet[DATASETTABLE_COLUMN_FILE] = Path(file.io).stem

        return self.parse_rows(sheet, table_names, *args, **kwargs)

    def parse_rows(
        self,
        sheet: pd.DataFrame,
        table_names: List[str] = None,
        dataset_definitions: DatasetDefinition = None,
        *args,
        **kwargs,
    ) -> DatasetTable | None:

        main_table = None
        if (
            table_names
            and len(table_names) >= 1
            and table_names[0].startswith(DATASETTABLE_SHEET_TABLES_MAIN_PREFIX)
        ):
            main_table = table_names[0]

        # Generate column with database table names
        sheet[COLUMN_TEMP_TABLE] = [
            main_table
            if pd.notna(type_) and type_ == DATASETTABLE_TYPE_HEADER
            else type_
            if pd.notna(type_) and all(entry not in type_ for entry in ["Group", "Matrix"])
            else None
            for type_ in sheet[DATASETTABLE_COLUMN_TYPE]
        ]
        sheet[COLUMN_TEMP_TABLE] = sheet[COLUMN_TEMP_TABLE].ffill()
        if main_table:
            sheet[COLUMN_TEMP_TABLE] = sheet[COLUMN_TEMP_TABLE].fillna(value=main_table)

        if dataset_definitions:
            # Update table name from dataset definitions
            sheet[COLUMN_TEMP_TABLE] = [
                dataset_definitions.get_correct_full_table_names(table, item)
                for table, item in zip(
                    sheet[COLUMN_TEMP_TABLE], sheet[DATASETTABLE_COLUMN_VARIABLE]
                )
            ]

        subgroup_map = {}
        for table in sheet[COLUMN_TEMP_TABLE].unique():
            if len(parts := table.split(":")) > 1:
                group = parts[0]
                if group not in subgroup_map:
                    subgroup_map[group] = []
                subgroup_map[group].append(parts[1])

        # Fill category
        sheet[Columns.HEADER.value] = [
            question if type_ == DATASETTABLE_TYPE_HEADER else None
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
        ]
        sheet[Columns.HEADER.value] = sheet[Columns.HEADER.value].ffill()

        subgroups = {
            type_: question
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
            if pd.notna(type_) and type_.startswith("emnp")
        }

        sheet[Columns.HEADER.value] = [
            generate_header(header, subgroups.get(table.split(":")[-1]) if table else None)
            for header, table in zip(sheet[Columns.HEADER.value], sheet[COLUMN_TEMP_TABLE])
        ]

        # Remove all entries without items and variable names
        sheet.dropna(subset=[DATASETTABLE_COLUMN_ITEM, DATASETTABLE_COLUMN_DB_COLUMN], inplace=True)

        # Fill down questions to sub-items
        sheet[DATASETTABLE_COLUMN_QUESTION] = sheet[DATASETTABLE_COLUMN_QUESTION].ffill()

        # Rename columns
        mappings = {
            DATASETTABLE_COLUMN_ITEM: Columns.ITEM.value,
            DATASETTABLE_COLUMN_SHEET_NAME: Columns.SHEET.value,
            DATASETTABLE_COLUMN_FILE: Columns.FILE.value,
            DATASETTABLE_COLUMN_QUESTION: Columns.QUESTION.value,
            DATASETTABLE_COLUMN_VARIABLE: Columns.VARIABLE.value,
        }
        sheet.rename(columns=mappings, inplace=True)
        result = DatasetTable(sheet, subgroup_names=subgroups, subgroups=subgroup_map)

        # Create identifier column
        result.identifier = [
            generate_id(sheet, variable)
            for sheet, variable in zip(sheet[COLUMN_TEMP_TABLE], result.variable)
        ]
        result.uid = [
            generate_id(file, identifier, str(index))
            for file, identifier, index in zip(result.file, result.identifier, result.index)
        ]

        # Set options
        options = result.get(DATASETTABLE_COLUMN_OPTIONS)
        result.options = (
            [_generate_options(options_) for options_ in options] if options is not None else None
        )

        # Generate parameter
        result.parameter = [
            generate_parameter(header, question, item)
            for header, question, item in zip(result.header, result.question, result.item)
        ]

        result.drop_superfluous_columns()

        return result


def _get_meta(sheet: pd.DataFrame, entry_name: str) -> str | None:
    index, *_ = np.where(sheet[DATASETTABLE_COLUMN_PROJECT] == entry_name)
    return sheet.loc[index[0]][2] if index else None


def generate_header(*args) -> List[str] | None:
    result = [entry for entry in args if entry]
    return result if result else None


def generate_parameter(*args) -> str:
    cleaned_args = list(dict.fromkeys(get_term_parts(*args)))
    return ":".join(cleaned_args)


def _generate_options(options: str) -> List[str] | None:
    return (
        options.replace(";", "\n").replace("\n\n", "\n").splitlines() if pd.notna(options) else None
    )
