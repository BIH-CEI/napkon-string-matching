import logging
from enum import Enum
from pathlib import Path
from typing import Dict

import pandas as pd
from napkon_string_matching.types.data import Data

logger = logging.getLogger(__name__)


class Columns(Enum):
    IDENTIFIER = "Identifier"
    PARAMETER = "Parameter"
    VARIABLE = "Variable"
    MATCH_SCORE = "MatchScore"
    MATCH_IDENTIFIER = "MatchIdentifier"
    MATCH_PARAMETER = "MatchParameter"
    MATCH_VARIABLE = "MatchVariable"


class Comparable(Data):
    __slots__ = [column.name.lower() for column in Columns]
    __columns__ = Columns

    def write_csv(self, file_name: str | Path) -> None:
        file = Path(file_name)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)

        logger.info("prepare result data for output...")

        logger.info("write result to %s", str(file))
        file.write_text(self.to_csv(index=False), encoding="utf-8")


class ComparisonResults:
    def __init__(self, comp_dict: Dict[str, Comparable] = None) -> None:
        self.results = comp_dict if comp_dict else {}

    def __setitem__(self, item, value):
        self.results[item] = value

    def __getitem__(self, item):
        return self.results[item]

    def items(self):
        return self.results.items()

    def write_excel(self, file: str):
        path = Path(file)
        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        logger.info("write result to file %s", str(file))
        writer = pd.ExcelWriter(file, engine="openpyxl")
        for name, comp in self.items():
            comp.to_excel(writer, sheet_name=name, index=False)
        writer.save()
