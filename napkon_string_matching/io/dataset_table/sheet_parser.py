"""
Module for the SheetParser
"""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from napkon_string_matching.io.dataset_table import constants as tc


class SheetParser:
    """
    A parser for sheets of a dataset table
    """

    def __init__(self) -> None:
        self.current_categories = []
        self.current_question = None

    def parse(self, file: pd.ExcelFile, sheet_name: str) -> List[dict]:
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
            file, sheet_name=sheet_name, na_values=tc.ITEM_SKIPABLE
        )

        # Remove leading meta information block on sheet
        start_index = np.where(sheet[tc.COLUMN_PROJECT] == tc.COLUMN_NUMBER)[0][0]
        sheet.columns = sheet.iloc[start_index]
        sheet = sheet.iloc[(start_index) + 1 :, :].reset_index(drop=True)

        # Replace `NaN` with `None` for easier handling
        sheet.where(pd.notnull(sheet), None, inplace=True)

        # Add meta information to each row
        sheet[tc.COLUMN_SHEET_NAME] = sheet_name
        sheet[tc.COLUMN_FILE] = file.io

        results = []
        for _, row in sheet.iterrows():
            if item := self._parse_row(row):
                results.append(item)

        return results

    def _parse_row(self, row: pd.Series) -> Dict[str, Any] | None:
        # Extract information like header and question for following entries
        if type_ := row[tc.COLUMN_TYPE]:
            question_entry = row[tc.COLUMN_QUESTION]
            if type_ == tc.TYPE_HEADER:
                # If header the category is reset
                self.current_categories = (
                    [question_entry]
                    if question_entry and len(question_entry) > 1
                    else []
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

        if not row[tc.COLUMN_ITEM] or not row[tc.COLUMN_DB_COLUMN]:
            return None

        item = {
            "item": row[tc.COLUMN_ITEM],
            "sheet": row[tc.COLUMN_SHEET_NAME],
            "file": row[tc.COLUMN_FILE],
        }

        if self.current_categories:
            item["categories"] = self.current_categories
        if self.current_question:
            item["question"] = self.current_question

        if row[tc.COLUMN_OPTIONS]:
            # When reading these value they are not actually only separated by
            # semicolons but also by linebreaks. Special handling for cases
            # where only one of them is present
            item["options"] = (
                row[tc.COLUMN_OPTIONS]
                .replace(";", "\n")
                .replace("\n\n", "\n")
                .splitlines()
            )

        return item
