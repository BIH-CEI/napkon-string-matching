import enum
import json
import logging
from pathlib import Path

import pandas as pd


class Columns(enum.Enum):
    ITEM = "Item"
    SHEET = "Sheet"
    FILE = "File"
    CATEGORIES = "Categories"
    QUESTION = "Question"
    OPTIONS = "Options"
    TERM = "Term"
    TOKENS = "Tokens"
    TOKEN_IDS = "TokenIds"
    TOKEN_MATCH = "TokenMatch"
    IDENTIFIER = "Identifier"
    MATCHES = "Matches"
    VARIABLE = "Variable"


COLUMN_NAMES = [column.value for column in Columns]
PROPERTY_NAMES = [column.name.lower() for column in Columns]

logger = logging.getLogger(__name__)


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


class Questionnaire(Subscriptable):
    def __init__(self, data=None) -> None:
        self._data = pd.DataFrame(data)

    def concat(self, others: List):
        if len(others) == 0:
            return self

        if not isinstance(others[0], Questionnaire):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(others[0]).__name__
                )
            )

        return Questionnaire(
            pd.concat([self._data, *[other._data for other in others]], ignore_index=True)
        )

    @staticmethod
    def read_json(file: str | Path):
        """
        Read a `Questionnaire` stored as JSON from file

        Attributes
        ---
            file_path (str|Path):   file path to read from

        Returns
        ---
            Questionnaire:  from the file contents
        """

        logger.info("read from file %s...", str(file))

        file = Path(file)
        definition = json.loads(file.read_text(encoding="utf-8"))

        result = Questionnaire(definition)
        result.reset_index(drop=True, inplace=True)

        logger.info("...got %i entries", len(result))
        return result

    def write_json(self, file: str | Path) -> None:
        """
        Write a `Questionnaire` to file in JSON format

        Attributes
        ---
            file_path (str|Path):   file path to write to
        """

        logger.info("write %i entries to file %s...", len(self), str(file))

        file = Path(file)
        file.write_text(self.to_json(), encoding="utf-8")

        logger.info("...done")
