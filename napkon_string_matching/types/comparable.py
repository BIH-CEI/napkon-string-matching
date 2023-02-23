import json
import logging
from enum import Enum
from typing import Dict, List

import pandas as pd

from napkon_string_matching.types.base.readable_json import ReadableJson
from napkon_string_matching.types.base.writable_excel import WritableExcel
from napkon_string_matching.types.base.writable_json import WritableJson
from napkon_string_matching.types.data import Data

logger = logging.getLogger(__name__)


class Columns(Enum):
    IDENTIFIER = "Identifier"
    PARAMETER = "Parameter"
    VARIABLE = "Variable"
    SHEET = "Sheet"
    MATCH_SCORE = "MatchScore"


COLUMN_NAMES = [
    Columns.IDENTIFIER.value,
    Columns.PARAMETER.value,
    Columns.VARIABLE.value,
    Columns.SHEET.value,
]

LEFT_NAME = "left_name"
RIGHT_NAME = "right_name"
DATA_NAME = "data"


class Comparable(ReadableJson, WritableJson):
    left_name: str = None
    right_name: str = None
    data: Data = None

    def __init__(self, data=None, left_name: str = None, right_name: str = None):
        if left_name is not None and right_name is not None:
            object.__setattr__(self, "left_name", left_name)
            object.__setattr__(self, "right_name", right_name)
            object.__setattr__(self, "data", Data(data))
        elif LEFT_NAME in data and RIGHT_NAME in data and DATA_NAME in data:
            object.__setattr__(self, "left_name", data[LEFT_NAME])
            object.__setattr__(self, "right_name", data[RIGHT_NAME])
            object.__setattr__(self, "data", Data(data[DATA_NAME]))
        else:
            raise AttributeError(
                "Either provide 'left_name' AND 'right_name' or a dictionary in 'data' providing the "
                f"entries {LEFT_NAME}, {RIGHT_NAME} AND {DATA_NAME}"
            )

    def to_json(self, orient: str | None = None, *args, **kwargs):
        result = {
            LEFT_NAME: self.left_name,
            RIGHT_NAME: self.right_name,
            DATA_NAME: self.data.to_dict(orient=orient),
        }
        return json.dumps(result, *args, **kwargs)

    def sort_by_score(self) -> None:
        self._data.sort_values(by=Columns.MATCH_SCORE.value, ascending=False, inplace=True)

    def __getitem__(self, item):
        result = self.data[item]
        if isinstance(result, Data):
            return self.__class__(data=result, left_name=self.left_name, right_name=self.right_name)
        return result

    def __getattr__(self, name: str):
        name_parts = name.split("_")
        if name_parts[-1].title() in COLUMN_NAMES:
            if name_parts[0] == "match":
                return self.data[self.left_name + name_parts[-1].title()]
            else:
                return self.data[self.right_name + name_parts[-1].title()]
        elif name == Columns.MATCH_SCORE.name.lower():
            return self.data[Columns.MATCH_SCORE.value]
        else:
            return getattr(self.data, name)

    def __setattr__(self, name: str, value) -> None:
        name_parts = name.split("_")
        if name_parts[-1].title() in COLUMN_NAMES:
            if name_parts[0] == "match":
                self.data[self.left_name + name_parts[-1].title()] = value
            else:
                self.data[self.right_name + name_parts[-1].title()] = value
        elif name == Columns.MATCH_SCORE.name.lower():
            self.data[Columns.MATCH_SCORE.value] = value
        else:
            setattr(self.data, name, value)

    def __repr__(self) -> str:
        return repr(self.data)

    def __str__(self) -> str:
        return str(self.data)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Comparable):
            return False
        return (
            self.left_name == __o.left_name
            and self.right_name == __o.right_name
            and self.data.equals(__o.data)
        )

    def __len__(self) -> int:
        return len(self.data)

    def dropna(self, *args, **kwargs):
        return self.__class__(
            data=self._data.dropna(*args, **kwargs),
            left_name=self.left_name,
            right_name=self.right_name,
        )

    def drop(self, *args, **kwargs):
        return self.__class__(
            data=self._data.drop(*args, **kwargs),
            left_name=self.left_name,
            right_name=self.right_name,
        )

    def merge(self, *args, **kwargs):
        return self.__class__(
            data=self._data.merge(*args, **kwargs),
            left_name=self.left_name,
            right_name=self.right_name,
        )

    def dataframe(self) -> pd.DataFrame:
        return self.data.dataframe()

    def drop_superfluous_columns(self, columns: List[str] = None) -> None:
        self.data.drop_superfluous_columns(self.__column_names__ if columns is None else columns)


class ComparisonResults(WritableExcel):
    def __init__(self, comp_dict: Dict[str, Comparable] = None) -> None:
        self.results = comp_dict if comp_dict else {}

    def __setitem__(self, item, value):
        self.results[item] = value

    def __getitem__(self, item):
        return self.results[item]

    def items(self):
        return self.get_items()

    def get_items(self):
        return self.results.items()
