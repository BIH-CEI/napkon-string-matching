import re
import warnings
from typing import Dict, List

import pandas as pd

from napkon_string_matching.types.mapping import Mapping


class MatchedMapping(Mapping):
    @classmethod
    def read_excel(cls, file_path: str, match_value: int = 1):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            excel_file = pd.ExcelFile(file_path, engine="openpyxl")

        sheet_name_regex = re.compile(r"^(var_)?(?P<first>\w+)\svs\s(?P<second>\w+)$")
        sheet_names: List[str] = excel_file.sheet_names
        result: Dict[str, Dict[str, Dict[str, str]]] = {}
        for sheet_name in sheet_names:
            sheet = excel_file.parse(sheet_name=sheet_name)

            match: re.Match[str] = sheet_name_regex.match(sheet_name)
            name_left, name_right = match.group("first"), match.group("second")
            decision_colum_left = f"Entscheidung {name_left.upper()}"
            decision_colum_right = f"Entscheidung {name_right.upper()}"
            identifier_colum_left = f"{name_left.title()}Identifier"
            identifier_colum_right = f"{name_right.title()}Identifier"

            matches = [
                (il, ir)
                for dl, dr, il, ir in zip(
                    sheet[decision_colum_left],
                    sheet[decision_colum_right],
                    sheet[identifier_colum_left],
                    sheet[identifier_colum_right],
                )
                if not (dl is None or dr is None)
                and (dl == match_value or pd.isna(dl))
                and (dr == match_value or pd.isna(dr))
            ]

            if name_left not in result:
                result[name_left] = {}
            if name_right not in result[name_left]:
                result[name_left][name_right] = {}
            update = {left: right for left, right in matches}
            result[name_left][name_right].update(update)

            if name_right not in result:
                result[name_right] = {}
            if name_left not in result[name_right]:
                result[name_right][name_left] = {}
            update = {right: left for left, right in matches}
            result[name_right][name_left].update(update)

        return cls(data=result)
