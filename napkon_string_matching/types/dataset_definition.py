import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd
from napkon_string_matching.types.identifier import TABLE_SEPARATOR

logger = logging.getLogger(__name__)

COLUMN_TABLE = "Table"
COLUMN_VARIABLE = "Variable"

DEFINITION_TABLE_ITEMS = "table_items"
DEFINITION_SUBTABLES = "subtables"


class DatasetDefinition:
    def __init__(self, data: Dict[str, Dict[str, List[str]]] = None):
        self._table_items: DefinitionTableItems = None
        self._subtables: DefinitionSubtables = None

        if data:
            if table_items := data.get(DEFINITION_TABLE_ITEMS):
                self._table_items = DefinitionTableItems(table_items)

            if subtables := data.get(DEFINITION_SUBTABLES):
                self._subtables = DefinitionSubtables(subtables)

        if not self._table_items:
            self._table_items = DefinitionTableItems()
        if not self._subtables:
            self._subtables = DefinitionSubtables()

    @property
    def table_items(self):
        return self._table_items

    @property
    def subtables(self):
        return self._subtables

    def get_correct_full_table_names(self, table: str, item: str) -> str:
        # Split the table string into the different table names
        table_names = table.split(TABLE_SEPARATOR)
        table_name = table_names[-1]

        # Get the (updated) correct table name
        new_table_name = self._get_correct_table_name(table_name, item)

        # Check if there is a parent table
        parent_table = self.subtables.get_parent(new_table_name)

        # Return combined table string
        if parent_table:
            new_table_name = f"{parent_table}{TABLE_SEPARATOR}{new_table_name}"
        return new_table_name

    def _get_correct_table_name(self, table: str, item: str) -> str:
        if not item:
            return table

        # If the item is already correct just return the current name
        if table and self.table_items.in_table(table, item):
            return table
        # Otherwise, search for the correct one
        else:
            new_table = self.table_items.get_table_name(item)
            if new_table:
                return new_table
            else:
                logger.info("did not find table for '%s', returning previous '%s'", item, table)
                return table

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            DEFINITION_TABLE_ITEMS: self._table_items.to_dict(),
            DEFINITION_SUBTABLES: self._subtables.to_dict(),
        }

    @classmethod
    def read_csv(cls, column_file: str | Path, dataset_file: str | Path):
        dataset = DatasetDefinition()
        dataset._table_items = DefinitionTableItems.read_csv(column_file)
        dataset._subtables = DefinitionSubtables.read_csv(dataset_file)
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

    def add_from_file(self, item: str, column_file: str | Path, dataset_file: str | Path) -> None:
        self[item] = DatasetDefinition.read_csv(column_file, dataset_file)


class DefinitionTableItems:
    def __init__(self, data: Dict[str, List[str]] = None):
        self.data = data if data else {}

    def __getitem__(self, item: str) -> List[str]:
        return self.data.get(item, list())

    def __setitem__(self, item: str, value: List[str]) -> None:
        self.data[item] = value

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def in_table(self, table: str, item: str) -> bool:
        return item in self[table]

    def get_table_name(self, item) -> str | None:
        for table, items in self.data.items():
            if item in items:
                return table
        return None

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


class DefinitionSubtables:
    def __init__(self, data: Dict[str, List[str]] = None):
        self.data = data if data else {}

    def __getitem__(self, item: str) -> List[str]:
        return self.data.get(item, list())

    def __setitem__(self, item: str, value: List[str]) -> None:
        self.data[item] = value

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def get_parent(self, table: str) -> str:
        for parent, tables in self.data.items():
            if table in tables:
                return parent
        return None

    def to_dict(self) -> Dict[str, List[str]]:
        return deepcopy(self.data)

    @classmethod
    def read_csv(cls, file: str | Path):
        logger.info("read from file %s...", str(file))
        df: pd.DataFrame = pd.read_csv(file, usecols=[3])
        result = cls()
        for table_string in pd.unique(df.iloc[:, 0]):
            tables = table_string.split(", ")
            if len(tables) <= 1:
                continue
            table = tables[0]
            subtables = tables[1:]
            table = table.lower()
            if table in result:
                logger.warning(
                    "cannot assign subtables %s to table %s, already assigned %s",
                    subtables,
                    table,
                    result[table],
                )
                continue
            result[table] = subtables
        logger.info("got %i tables", len(result.data.keys()))
        return result
