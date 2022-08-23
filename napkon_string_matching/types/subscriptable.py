from operator import getitem, setitem

import pandas as pd


class Subscriptable:
    __slots__ = ["_data"]
    __columns__ = []

    def __new__(cls, *args, **kwargs):
        # Automatically define setter and getter methods for all properties
        for column in cls.__columns__:
            property_name = column.name.lower()

            def getter_method(column=column.value):
                return lambda self: getitem(self._data, column)

            def setter_method(column=column.value):
                return lambda self, value: setitem(self._data, column, value)

            setattr(
                cls,
                property_name,
                property(
                    fget=getter_method(),
                    fset=setter_method(),
                ),
            )

            cls.__column_names__ = [column.value for column in cls.__columns__]
        return super().__new__(cls)

    def __init__(self, data=None):
        self._data = pd.DataFrame(data)

    def __getattr__(self, __name: str):
        return getattr(self._data, __name)

    def __getitem__(self, val):
        result = self._data.__getitem__(val)
        if isinstance(result, pd.DataFrame):
            return self.__class__(result)
        else:
            return result

    def __repr__(self) -> str:
        return repr(self._data)

    def __str__(self) -> str:
        return str(self._data)

    def __eq__(self, __o: object) -> bool:
        return self._data.equals(__o)

    def __len__(self) -> int:
        return len(self._data)

    def dropna(self, *args, **kwargs):
        return self.__class__(self._data.dropna(*args, **kwargs))

    def drop(self, *args, **kwargs):
        return self.__class__(self._data.drop(*args, **kwargs))

    def merge(self, *args, **kwargs):
        return self.__class__(self._data.merge(*args, **kwargs))

    def dataframe(self) -> pd.DataFrame:
        return self._data

    def drop_superfluous_columns(self) -> None:
        remove_columns = set(self.columns).difference(set(self.__column_names__))
        self.drop(columns=remove_columns, inplace=True)
