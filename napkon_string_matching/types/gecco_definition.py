import logging
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import Dict, List

import napkon_string_matching.types.comparable as comp
import pandas as pd
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    CATEGORY = "Category"
    PARAMETER = "Parameter"
    CHOICES = "Choices"


logger = logging.getLogger(__name__)


class GeccoBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.CATEGORY.value


class GeccoCategory(GeccoBase, Category):
    pass


class GeccoDefinition(GeccoBase, ComparableData):
    __column_mapping__ = {ComparableColumns.IDENTIFIER.value: comp.Columns.VARIABLE.value}
    __category_type__ = GeccoCategory

    @staticmethod
    def read_gecco83_definition(file: str | Path):
        column_mapping = {
            "ID": ComparableColumns.IDENTIFIER.value,
            "KATEGORIE": Columns.CATEGORY.value,
            "PARAMETER CASE REPORT FORM": Columns.PARAMETER.value,
            "ANTWORT-MÖGLICHKEITEN": Columns.CHOICES.value,
        }
        return GeccoDefinition._read_definition(
            file, column_mapping, choice_sep="|", id_prefix="gecco_"
        )

    @staticmethod
    def read_original_format(file_name, *args, **kwargs):
        return GeccoDefinition.read_json(file_name, *args, **kwargs)

    @staticmethod
    def read_geccoplus_definition(file: str | Path, *args, **kwargs):
        column_mapping = {
            "ID": ComparableColumns.IDENTIFIER.value,
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

        # Trim all whitespaces
        gecco.identifier = _strip_column(gecco.identifier)
        gecco.category = _strip_column(gecco.category)
        gecco.parameter = _strip_column(gecco.parameter)
        gecco.choices = _strip_column(gecco.choices)

        gecco.choices = [
            [choice.strip() for choice in entry.strip().split(choice_sep)]
            if pd.notna(entry)
            else None
            for entry in gecco.choices
        ]

        gecco.category = [category.title().replace(" ", "") for category in gecco.category]

        rows = []
        for _, row in gecco.iterrows():
            if not isinstance(row[Columns.CHOICES.value], list):
                rows.append(row)
                continue

            for index, choice in enumerate(row[Columns.CHOICES.value]):
                new_row = row.copy(deep=True)
                new_row[Columns.CHOICES.value] = choice
                if index != 0:
                    new_row[ComparableColumns.IDENTIFIER.value] = None
                rows.append(new_row)

        gecco = GeccoDefinition(rows)

        gecco.reset_index(inplace=True)

        gecco.identifier = _fill_id_gaps(gecco.identifier)
        gecco.identifier = id_prefix + gecco.identifier

        return gecco

    def concat(self, other):
        if not isinstance(other, GeccoDefinition):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(other).__name__
                )
            )

        return GeccoDefinition(pd.concat([self._data, other._data], ignore_index=True))

    def add_terms(self, language: str = "german"):
        logger.info("add terms...")
        result = [
            ComparableData.gen_term([category, parameter], language=language)
            for category, parameter in zip(self.category, self.parameter)
        ]
        self.term = result
        logger.info("...done")


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
