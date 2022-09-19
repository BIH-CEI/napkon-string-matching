import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

COLUMN_TABLE = "Table"
COLUMN_VARIABLE = "Variable"


class DatasetDefinition:
    def __init__(self, data: Dict[str, List[str]] = None):
        self.data = data if data else {}

    def __getitem__(self, item: str) -> List[str]:
        return self.data.get(item, list())

    def __setitem__(self, item: str, value: List[str]) -> None:
        self.data[item] = value

    def to_dict(self) -> Dict[str, List[str]]:
        return deepcopy(self.data)

    @classmethod
    def read_csv(cls, file: str | Path):
        logger.info("read from file %s...", str(file))
        df: pd.DataFrame = pd.read_csv(file, names=[COLUMN_TABLE, COLUMN_VARIABLE], usecols=[3, 4])
        dataset = DatasetDefinition()
        for _, row in df.iterrows():
            item = row[COLUMN_TABLE].replace(", ", ":")
            value = row[COLUMN_VARIABLE]
            dataset[item] = [*dataset[item], value]
        logger.info("got %i tables", len(dataset.data.keys()))
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

    def add_from_file(self, item: str, file: str | Path) -> None:
        self[item] = DatasetDefinition.read_csv(file)
