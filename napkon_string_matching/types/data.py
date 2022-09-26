import logging
from hashlib import md5
from operator import getitem, setitem
from pathlib import Path
from typing import List

import pandas as pd
from napkon_string_matching.types.readable_json_frame import ReadableJsonFrame
from napkon_string_matching.types.writable_json import WritableJson

logger = logging.getLogger(__name__)


class Data(ReadableJsonFrame, WritableJson):
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
        if isinstance(data, Data):
            self._data = data
        else:
            self._data = pd.DataFrame(data)

    def __getattr__(self, __name: str):
        return getattr(self._data, __name)

    def __getitem__(self, val):
        result = self._data.__getitem__(val)
        if isinstance(result, pd.DataFrame):
            return self.__class__(result)
        else:
            return result

    def __setitem__(self, item, value):
        setitem(self._data, item, value)

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

    def drop_superfluous_columns(self, columns: List[str] = None) -> None:
        remove_columns = set(self.columns).difference(
            set(columns if columns is not None else self.__column_names__)
        )
        self.drop(columns=remove_columns, inplace=True)

    def write_csv(self, file_name: str | Path, *args, **kwargs) -> None:
        """
        Write data to file in JSON format

        Attributes
        ---
            file_path (str|Path):   file path to write to
        """

        logger.info("write %i entries to file %s...", len(self), str(file_name))

        file = Path(file_name)
        file.write_text(self.to_csv(index=False), encoding="utf-8")

        logger.info("...done")

    def write_excel(self, file_name: str | Path):
        logger.info("write %i entries to file %s...", len(self), str(file_name))

        file = Path(file_name)
        writer = pd.ExcelWriter(file, engine="openpyxl")
        self._data.to_excel(writer, index=False)
        writer.save()

        logger.info("...done")

    def to_json(self, *args, **kwargs):
        return self._data.to_json(*args, **kwargs)

    def hash(self) -> str:
        return gen_hash(self._data.to_csv())


def gen_hash(string: str) -> str:
    return md5(string.encode("utf-8"), usedforsecurity=False).hexdigest()
