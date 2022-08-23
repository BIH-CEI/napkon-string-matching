import enum
import json
import logging
import re
import warnings
from pathlib import Path
from typing import Dict, List

import pandas as pd
from napkon_string_matching.types.subscriptable import Subscriptable


class Columns(enum.Enum):
    ID = "Id"
    CATEGORY = "Category"
    PARAMETER = "Parameter"
    CHOICES = "Choices"


logger = logging.getLogger(__name__)


class GeccoDefinition(Subscriptable):
    __slots__ = [column.name.lower() for column in Columns]
    __columns__ = Columns

    @staticmethod
    def read_gecco83_definition(file: str | Path):
        column_mapping = {
            "ID": Columns.ID.value,
            "KATEGORIE": Columns.CATEGORY.value,
            "PARAMETER CASE REPORT FORM": Columns.PARAMETER.value,
            "ANTWORT-MÖGLICHKEITEN": Columns.CHOICES.value,
        }
        return GeccoDefinition._read_definition(
            file, column_mapping, choice_sep="|", id_prefix="gecco_"
        )

    @staticmethod
    def read_geccoplus_definition(file: str | Path):
        column_mapping = {
            "ID": Columns.ID.value,
            "Kategorie": Columns.CATEGORY.value,
            "Data Item": Columns.PARAMETER.value,
            "Antwortausprägungen": Columns.CHOICES.value,
        }
        return GeccoDefinition._read_definition(
            file, column_mapping, choice_sep="\n", id_prefix="gecco_83+"
        )

    @staticmethod
    def _read_definition(
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

        return GeccoDefinition(pd.concat([self._data, other._data], ignore_index=True))

    @staticmethod
    def read_json(file: str | Path):
        file = Path(file)
        definition = json.loads(file.read_text(encoding="utf-8"))
        result = GeccoDefinition(definition)
        result.reset_index(drop=True, inplace=True)
        return result

    def write_json(self, file: str | Path) -> None:
        file = Path(file)
        file.write_text(self.to_json(), encoding="utf-8")


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
