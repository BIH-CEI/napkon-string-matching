from typing import List

import pandas as pd


class Category:
    __category_column__ = None
    __columns__ = []
    __column_names__ = ""

    def __new__(cls, *args, **kwargs):
        cls.__column_names__ = [column.value for column in cls.__columns__]
        return super().__new__(cls)

    def __init__(self, data: pd.DataFrame, category: str) -> None:
        self._data = data
        self.category = category

    @property
    def is_category(self) -> List[bool]:
        return [
            self.entry_matches_category(entry) for entry in self._data[self.__category_column__]
        ]

    def entry_matches_category(self, entry):
        if self.category is None:
            return not bool(entry)
        else:
            if isinstance(entry, list):
                return self.category in entry
            else:
                return self.category == entry

    @property
    def dataframe(self):
        return self._data.loc[self.is_category, :]

    def __getitem__(self, column: str):
        if column in self.__column_names__:
            return self._data.loc[self.is_category, column]
        else:
            raise KeyError("Column '%s' not found", column)

    def __setitem__(self, column: str, value):
        if column in self.__column_names__:
            self._data.loc[self.is_category, column] = value
        else:
            raise KeyError("Column '{}' not found", column)

    def __repr__(self) -> str:
        return repr(self.dataframe)

    def __str__(self) -> str:
        return str(self.dataframe)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Category):
            return self.dataframe.equals(__o.dataframe)
        return False

    def __len__(self) -> int:
        return len(self.dataframe)
