import logging
import re
import warnings
from pathlib import Path
from typing import Dict, List

import pandas as pd
from napkon_string_matching.types.comparable_data import ComparableColumns
from napkon_string_matching.types.gecco_definition import Columns, GeccoDefinition

logger = logging.getLogger(__name__)


class GeccoExcelDefinition(GeccoDefinition):
    @classmethod
    def _read_definition(
        cls, file: str | Path, column_mapping: Dict[str, str], choice_sep: str, id_prefix: str = ""
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
        gecco = cls(df)

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

        gecco = cls(rows)

        gecco.reset_index(inplace=True)

        gecco.identifier = _fill_id_gaps(gecco.identifier)
        gecco.identifier = id_prefix + gecco.identifier

        return gecco


def _strip_column(column: pd.Series) -> pd.Series:
    return [
        re.sub(r"[\xa0]", "", str(entry)).replace("<br>", "").strip()
        if not pd.isna(entry)
        else None
        for entry in column
    ]


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
