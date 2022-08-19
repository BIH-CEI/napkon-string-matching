import enum
import logging
import re
import warnings
from pathlib import Path
from typing import Dict, List

import pandas as pd


class Columns(enum.Enum):
    ID = "Id"
    CATEGORY = "Category"
    PARAMETER = "Parameter"
    CHOICES = "Choices"


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


class GeccoDefinition(Subscriptable):
    def __init__(self, data) -> None:
        self._data = pd.DataFrame(data)

    @staticmethod
    def from_gecco83_definition(file: str | Path):
        column_mapping = {
            "ID": Columns.ID.value,
            "KATEGORIE": Columns.CATEGORY.value,
            "PARAMETER CASE REPORT FORM": Columns.PARAMETER.value,
            "ANTWORT-MÖGLICHKEITEN": Columns.CHOICES.value,
        }
        return GeccoDefinition._from_definition(
            file, column_mapping, choice_sep="|", id_prefix="gecco_"
        )

    @staticmethod
    def from_geccoplus_definition(file: str | Path):
        column_mapping = {
            "ID": Columns.ID.value,
            "Kategorie": Columns.CATEGORY.value,
            "Data Item": Columns.PARAMETER.value,
            "Antwortausprägungen": Columns.CHOICES.value,
        }
        return GeccoDefinition._from_definition(
            file, column_mapping, choice_sep="\n", id_prefix="gecco_83+"
        )

    @staticmethod
    def _from_definition(
        file: str | Path, column_mapping: Dict[str, str], choice_sep: str, id_prefix: str = ""
    ):
        file = Path(file)

        logger.info("read from file %s...", str(file))

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            excel_file = pd.ExcelFile(file, engine="openpyxl")

        df: pd.DataFrame = excel_file.parse()

        # Remove whitespaces in column names
        df.columns = [column.strip() for column in df.columns]

        # Rename columns to fit common names
        df.rename(columns=column_mapping, inplace=True)

        # Create new type
        gecco = GeccoDefinition(df)

        # Remove empty lines
        gecco.dropna(how="all", inplace=True)
        gecco.dropna(
            how="any", subset=[Columns.CATEGORY.value, Columns.PARAMETER.value], inplace=True
        )
        gecco.reset_index(inplace=True)

        # Trim all whitespaces
        gecco.id = _strip_column(gecco.id)
        gecco.category = _strip_column(gecco.category)
        gecco.parameter = _strip_column(gecco.parameter)
        gecco.choices = _strip_column(gecco.choices)

        gecco.id = _fill_id_gaps(gecco.id)

        gecco.choices = [
            [choice.strip() for choice in entry.strip().split(choice_sep)] if entry else None
            for entry in gecco.choices
        ]

        gecco.id = id_prefix + gecco.id

        return gecco

    def concat(self, other):
        if not isinstance(other, GeccoDefinition):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(other).__name__
                )
            )

        return GeccoDefinition(pd.concat([self._data, other._data]))


def _strip_column(column: pd.Series) -> pd.Series:
    return [str(entry).replace("\xa0", "") if not pd.isna(entry) else None for entry in column]


def _fill_id_gaps(id_column: pd.Series) -> List:
    result = []
    length = len(id_column)
    regex = re.compile(r"(\d+-)(\d+)")
    for index, id_ in enumerate(id_column):
        prev = result[index - 1] if index > 0 else -1
        next_ = id_column[index + 1] if index < length - 1 else -1

        if not id_:
            matches = regex.match(prev)
            new_id = matches.group(1) + str(int(matches.group(2)) + 1)
        elif not next_:
            new_id = id_ + "-1"
        else:
            new_id = id_

        result.append(new_id)

    return result
