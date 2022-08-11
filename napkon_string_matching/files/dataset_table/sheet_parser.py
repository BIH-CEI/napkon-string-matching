"""
Module for the SheetParser
"""

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
from napkon_string_matching.files.dataset_table import (
    DATASETTABLE_COLUMN_DB_COLUMN,
    DATASETTABLE_COLUMN_FILE,
    DATASETTABLE_COLUMN_ITEM,
    DATASETTABLE_COLUMN_NUMBER,
    DATASETTABLE_COLUMN_OPTIONS,
    DATASETTABLE_COLUMN_PROJECT,
    DATASETTABLE_COLUMN_QUESTION,
    DATASETTABLE_COLUMN_SHEET_NAME,
    DATASETTABLE_COLUMN_TYPE,
    DATASETTABLE_COLUMN_VARIABLE,
    DATASETTABLE_ITEM_SKIPABLE,
    DATASETTABLE_TYPE_HEADER,
)


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
