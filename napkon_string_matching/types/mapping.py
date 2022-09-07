import json
import re
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

COLUMN_REGEX = re.compile(r"^([a-zA-Z]+)_([a-zA-Z\u00C0-\u00FC]+)_([a-zA-Z]+)$")


class MappingTarget:
    def __init__(self, data: Dict[str, str] = None) -> None:
        self._data: Dict[str, str] = data if data else {}

    def __getitem__(self, item) -> str:
        return self._data[item]

    def __setitem__(self, item, value) -> None:
        self._data[item] = value

    def dict(self) -> Dict[str, str]:
        return self._data

    def __repr__(self) -> str:
        return f"MappingTarget({repr(self._data)})"

    def __str__(self) -> str:
        return str(self._data)


class MappingSource:
    __items__ = ["hap", "gecco", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, str]] = None) -> None:
        for item in self.__items__:
            if data and item in data:
                self[item] = MappingTarget(data[item])
            else:
                self[item] = MappingTarget()

    def __getitem__(self, item) -> MappingTarget:
        if item not in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item not in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in self.__items__}

    def _repr_helper(self) -> str:
        return ",".join({f"{item}={repr(self[item])}" for item in self.__items__})

    def __repr__(self) -> str:
        return f"MappingSource({self._repr_helper()})"

    def __str__(self) -> str:
        return f"({self._repr_helper})"


class HapMappingSource(MappingSource):
    __items__ = ["gecco", "pop", "suep"]


class PopMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "suep"]


class SuepMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "pop"]


class Mapping:
    __items__ = ["hap", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, Dict[str, str]]] = None) -> None:
        self.hap: MappingSource = None
        self.pop: MappingSource = None
        self.suep: MappingSource = None

        class_map = {
            "hap": HapMappingSource,
            "pop": PopMappingSource,
            "suep": SuepMappingSource,
        }

        for item in self.__items__:
            if data and item in data:
                self[item] = class_map[item](data[item])
            else:
                self[item] = class_map[item]()

    def __getitem__(self, item) -> MappingSource:
        if item not in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item not in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in Mapping.__items__}

    def __repr__(self) -> str:
        return f"Mapping({','.join({f'{item}={repr(self[item])}' for item in Mapping.__items__})})"

    def __str__(self) -> str:
        return f"({','.join({f'{item}={str(self[item])}' for item in Mapping.__items__})})"

    @staticmethod
    def read_json(file: str | Path):
        content = json.loads(Path(file).read_text(encoding="utf-8"))
        return Mapping(data=content)

    def write_json(self, file: str | Path):
        dict_ = self.dict()
        Path(file).write_text(json.dumps(dict_), encoding="utf-8")

    @staticmethod
    def read_excel_napkon_dataset_core(file: str | Path):
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
