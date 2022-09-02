import pandas as pd


class Category:
    __category_column__ = None
    __column_names__ = ""

    def __new__(cls, *args, **kwargs):
        cls.__column_names__ = [column.value for column in cls.__columns__]
        return super().__new__(cls)

    def __init__(self, data: pd.DataFrame, category: str) -> None:
        self._data = data
        self.category = category

    @property
    def dataframe(self):
        return self._data.loc[self._data[self.__category_column__] == self.category, :]

    def __getitem__(self, column: str):
        if column in self.__column_names__:
            return self._data.loc[self._data[self.__category_column__] == self.category, column]
        else:
            raise KeyError("Column '%s' not found", column)

    def __setitem__(self, column: str, value):
        if column in self.__column_names__:
            self._data.loc[self._data[self.__category_column__] == self.category, column] = value
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
