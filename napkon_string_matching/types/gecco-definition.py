import enum

import pandas as pd


class Columns(enum.Enum):
    ID = "Id"
    CATEGORY = "Category"
    PARAMETER = "Parameter"
    OPTIONS = "Options"


COLUMN_NAMES = [column.value for column in Columns]
PROPERTY_NAMES = [column.name.lower() for column in Columns]


class Subscriptable:
    __slots__ = PROPERTY_NAMES

    def __new__(cls, *args, **kwargs):
        # Automatically define setter and getter methods for all properties
        for column in Columns:
            property_name = column.name.lower()

            def getter_method(column=column.value):
                return lambda self: getattr(self._data, column)

            def setter_method(column=column.value):
                return lambda self, value: setattr(self._data, column, value)

            setattr(
                cls,
                property_name,
                property(
                    fget=getter_method(),
                    fset=setter_method(),
                ),
            )
        return super().__new__(cls)

    def __getattr__(self, __name: str):
        return getattr(self._data, __name)

    def __repr__(self) -> str:
        return repr(self._data)

    def __str__(self) -> str:
        return str(self._data)

    def __eq__(self, __o: object) -> bool:
        return self._data.equals(__o)

    def __len__(self) -> int:
        return len(self._data)


class GeccoDefinition(Subscriptable):
    def __init__(self, data) -> None:
        self._data = pd.DataFrame(data)
