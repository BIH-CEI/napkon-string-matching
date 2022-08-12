"""
Module for the SheetParser
"""

import logging
import warnings
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_FILE,
    DATA_COLUMN_IDENTIFIER,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_OPTIONS,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_SHEET,
    DATA_COLUMN_VARIABLE,
)

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

DATASETTABLE_ITEM_SKIPABLE = "<->"

logger = logging.getLogger(__name__)


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
    ) -> pd.DataFrame | None:
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
        sheet[DATASETTABLE_COLUMN_SHEET_NAME] = sheet_name
        sheet[DATASETTABLE_COLUMN_FILE] = Path(file.io).stem

        rows = []
        for _, row in sheet.iterrows():
            if item := self._parse_row(row, *args, **kwargs):
                rows.append(item)

        return pd.DataFrame(rows) if rows else None

    def _parse_row(
        self,
        row: pd.Series,
        filter_column: str = None,
        filter_prefix: str = None,
        *args,
        **kwargs,
    ) -> Dict[str, Any] | None:
        # Extract information like header and question for following entries
        if type_ := row.get(DATASETTABLE_COLUMN_TYPE, None):
            question_entry = row[DATASETTABLE_COLUMN_QUESTION]
            if type_ == DATASETTABLE_TYPE_HEADER:
                # If header the category is reset
                self.current_categories = (
                    [question_entry] if question_entry and len(question_entry) > 1 else []
                )
            elif any(entry in type_ for entry in ["Group", "Matrix"]):
                # set current question multiple items for the same question
                self.current_question = question_entry
            else:
                # These should be `sub-headers` with strange type names
                # for these the sub-header is added to the current categories
                if len(self.current_categories) > 1:
                    self.current_categories.pop()
                self.current_categories.append(question_entry)

        if (
            filter_column
            and filter_prefix
            and row[filter_column]
            and not row[filter_column].startswith(filter_prefix)
        ):
            return None

        if not row[DATASETTABLE_COLUMN_ITEM] or not row[DATASETTABLE_COLUMN_DB_COLUMN]:
            return None

        item = {
            DATA_COLUMN_ITEM: row[DATASETTABLE_COLUMN_ITEM],
            DATA_COLUMN_SHEET: row[DATASETTABLE_COLUMN_SHEET_NAME],
            DATA_COLUMN_FILE: row[DATASETTABLE_COLUMN_FILE],
            DATA_COLUMN_VARIABLE: row.get(DATASETTABLE_COLUMN_VARIABLE, None),
            DATA_COLUMN_IDENTIFIER: "#".join(
                [
                    row[DATASETTABLE_COLUMN_FILE],
                    row[DATASETTABLE_COLUMN_SHEET_NAME],
                    str(row.name),
                ]
            ).replace(" ", "-"),
        }

        item[DATA_COLUMN_CATEGORIES] = self.current_categories if self.current_categories else None
        item[DATA_COLUMN_QUESTION] = self.current_question if self.current_question else None

        if options := row.get(DATASETTABLE_COLUMN_OPTIONS, None):
            # When reading these value they are not actually only separated by
            # semicolons but also by linebreaks. Special handling for cases
            # where only one of them is present
            item[DATA_COLUMN_OPTIONS] = (
                options.replace(";", "\n").replace("\n\n", "\n").splitlines()
            )
        else:
            item[DATA_COLUMN_OPTIONS] = None

        return item


def read(xlsx_file: str | Path, *args, **kwargs) -> pd.DataFrame:
    """
    Read a xlsx file

    The contents are returned as a list of dictionaries containing the row contents
    and meta information.

    attr
    ---
        xlsx_file (str|Path): file to read

    returns
    ---
        List[dict]: parsed result
    """

    logger.info("read from file %s...", str(xlsx_file))

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        file = pd.ExcelFile(xlsx_file, engine="openpyxl")
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

    result = pd.concat(sheets)

    # Reset to get a valid continous index at the end
    result.set_index(DATA_COLUMN_IDENTIFIER, inplace=True)

    logger.info("...got %i entries", len(result))

    return result
