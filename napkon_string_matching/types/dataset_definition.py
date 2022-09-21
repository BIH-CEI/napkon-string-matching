import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

COLUMN_TABLE = "Table"
COLUMN_VARIABLE = "Variable"


DEFINITION_TABLE_ITEMS = "table_items"
DEFINITION_TABLE_NAMES = "table_names"


class DatasetDefinition:
    def __init__(self, data: Dict[str, Dict[str, List[str]]] = None):
        self._table_items: DefinitionTableItems = None
        self._table_names: DefinitionTableNames = None

        if data:
            if table_items := data.get(DEFINITION_TABLE_ITEMS):
                self._table_items = DefinitionTableItems(table_items)
            if table_names := data.get(DEFINITION_TABLE_NAMES):
                self._table_names = DefinitionTableNames(table_names)

        if not self._table_items:
            self._table_items = DefinitionTableItems()
        if not self._table_names:
            self._table_names = DefinitionTableNames()

    @property
    def table_items(self):
        return self._table_items

    @property
    def table_names(self):
        return self._table_names

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            DEFINITION_TABLE_ITEMS: self._table_items.to_dict(),
            DEFINITION_TABLE_NAMES: self._table_names.to_dict(),
        }

    @classmethod
    def read_csv(cls, column_file: str | Path, tables_file: str | Path):
        dataset = DatasetDefinition()
        dataset._table_items = DefinitionTableItems.read_csv(column_file)
        dataset._table_names = DefinitionTableNames.read_csv(tables_file)
        return dataset


class DatasetDefinitions:
    def __init__(self, data: Dict[str, Dict[str, List[str]]] = None):
        self.data = {key: DatasetDefinition(value) for key, value in data.items()} if data else {}

    def __getitem__(self, item: str) -> DatasetDefinition:
        return self.data.get(item)

    def __setitem__(self, item: str, value: DatasetDefinition) -> None:
        self.data[item] = value

    def to_dict(self) -> Dict[str, Dict[str, List[str]]]:
        return {key: value.to_dict() for key, value in self.data.items()}

    def write_json(self, file: str | Path) -> None:
        Path(file).write_text(json.dumps(self.to_dict(), indent=4))

    @classmethod
    def read_json(cls, file: str | Path):
        data = json.loads(Path(file).read_text())
        return cls(data)

    def add_from_file(self, item: str, column_file: str | Path, tables_file: str | Path) -> None:
        self[item] = DatasetDefinition.read_csv(column_file, tables_file)


class DefinitionTableItems:
    def __init__(self, data: Dict[str, List[str]] = None):
        self.data = data if data else {}

    def __getitem__(self, item: str) -> List[str]:
        return self.data.get(item, list())

    def __setitem__(self, item: str, value: List[str]) -> None:
        self.data[item] = value

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def to_dict(self) -> Dict[str, List[str]]:
        return deepcopy(self.data)

    @classmethod
    def read_csv(cls, file: str | Path):
        logger.info("read from file %s...", str(file))
        df: pd.DataFrame = pd.read_csv(file, usecols=[0, 1])
        result = cls()
        for _, row in df.iterrows():
            table, item = tuple(row)
            if item in ["MNPID", "MNPDID"]:
                continue
            table = table.lower()
            if table not in result:
                result[table] = []
            result[table].append(item.lower())
        logger.info("got %i tables", len(result.data.keys()))
        return result


class DefinitionTableNames:
    def __init__(self, data: Dict[str, str] = None):
        self.data = data if data else {}

    def __getitem__(self, item: str) -> str:
        return self.data.get(item, None)

    def __setitem__(self, item: str, value: str) -> None:
        self.data[item] = value

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def to_dict(self) -> Dict[str, str]:
        return deepcopy(self.data)

    @classmethod
    def read_csv(cls, file: str | Path):
        logger.info("read from file %s...", str(file))
        df: pd.DataFrame = pd.read_csv(file, usecols=[0, 2])
        result = cls()
        for _, row in df.iterrows():
            table, name = tuple(row)
            if table in result:
                logger.warning(
                    "could not assign %s, %s has already assigned the name %s",
                    name,
                    table,
                    result[table],
                )
                continue
            result[table.lower()] = name
        logger.info("got %i tables", len(result.data.keys()))
        return result
