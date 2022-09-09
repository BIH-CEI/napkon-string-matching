import re
import warnings
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from napkon_string_matching.types.mapping import Mapping

COLUMN_REGEX = re.compile(r"^([a-zA-Z]+)_([a-zA-Z\u00C0-\u00FC]+)_([a-zA-Z]+)$")


class DatasetCoreMapping(Mapping):
    @staticmethod
    def read_excel(file: str | Path):
        excel_file: pd.ExcelFile = None
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            excel_file = pd.ExcelFile(file, engine="openpyxl")

        mapping = Mapping()
        for sheet_name in excel_file.sheet_names:
            sheet = excel_file.parse(sheet_name)
            sheet_name = sheet_name.lower().replace("ü", "ue")
            groups = Mapping._get_groups(sheet.columns)
            for group in groups:
                gecco_column, napkon_column = Mapping._get_columns(group, sheet.columns)
                for gecco, napkon in zip(sheet[gecco_column], sheet[napkon_column]):
                    if pd.isna(napkon) or pd.isna(gecco):
                        continue
                    mapping[sheet_name].gecco[napkon] = gecco
        return mapping

    @staticmethod
    def _get_groups(columns: List[str]) -> List[str]:
        group_names = set()
        for column in columns:
            if match := COLUMN_REGEX.match(column):
                group_names.add(match.group(1))
        return list(group_names)

    @staticmethod
    def _get_columns(group_name: str, columns: List[str]) -> Tuple[str, str]:
        result = []
        for column in columns:
            match = COLUMN_REGEX.match(column)
            if match and match.group(1) == group_name:
                result.append(column)
        if len(result) != 2:
            raise Exception("got incorrect number of columns: {}", str(len(result)))
        return tuple(result)
