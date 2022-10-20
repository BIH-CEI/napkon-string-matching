import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from napkon_string_matching.constants import COHORTS
from napkon_string_matching.types.base.readable_json import ReadableJson
from napkon_string_matching.types.base.writable_json import WritableJson
from napkon_string_matching.types.dataset_table.definitions import DatasetTablesDefinitions

NAN = ["NaN", "Haupttabellenblatt (ohne Wiedergruppen)", "--"]


class TableCategories(ReadableJson, WritableJson):
    def __init__(self, data: Dict[str, Dict[str, List[str]]] | None = None) -> None:
        self.data = data if data is not None else {}

    def __getitem__(self, item) -> Dict[str, List[str]]:
        return self.data[item]

    def __setitem__(self, item, value) -> None:
        self.data[item] = value

    def __len__(self) -> int:
        return sum([len(entries) for entries in self.data.values()])

    @classmethod
    def read_excel(
        cls,
        excel_path: Path | str,
        tables_definitions: DatasetTablesDefinitions,
    ):
        excel_path = Path(excel_path)

        if not excel_path.exists():
            return

        result = TableCategories()
        excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
        for sheet_name in COHORTS:
            table_definitions = tables_definitions[sheet_name]

            sheet = excel_file.parse(sheet_name=sheet_name, na_values=NAN)

            sheet[sheet.columns[0]] = [
                _find_in_dict(entry, table_definitions.groups) for entry in sheet[sheet.columns[0]]
            ]
            org_columns = sheet.columns
            sheet[sheet.columns[1]] = [
                _find_in_dict(entry, table_definitions.subgroup_names)
                for entry in sheet[sheet.columns[1]]
            ]

            sheet.dropna(how="any", subset=sheet.columns[0], inplace=True)

            table_names = [
                ":".join([entry for entry in names if pd.notna(entry)])
                for names in zip(sheet[sheet.columns[0]], sheet[sheet.columns[1]])
            ]
            categories = [
                [category for category in categories if pd.notna(category)]
                for categories in zip(*[sheet[column] for column in org_columns[2:]])
            ]

            result[sheet_name] = {
                name: sorted(categories) for name, categories in zip(table_names, categories)
            }
        return result

    def to_json(self, orient=None, *args, **kwargs):
        return json.dumps(self.data, *args, **kwargs)


def _find_in_dict(value: str, dict_: Dict[str, str]) -> str | None:
    for key, value_ in dict_.items():
        if value_ == value:
            return key
    return None
