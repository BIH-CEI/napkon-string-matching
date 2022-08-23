import json
import logging
from enum import Enum
from pathlib import Path

from napkon_string_matching.types.subscriptable import Subscriptable

logger = logging.getLogger(__name__)


class Columns(Enum):
    IDENTIFIER = "Identifier"
    PARAMETER = "Parameter"
    VARIABLE = "Variable"
    MATCH_SCORE = "MatchScore"
    MATCH_IDENTIFIER = "MatchIdentifier"
    MATCH_PARAMETER = "MatchParameter"
    MATCH_VARIABLE = "MatchVariable"


class Comparable(Subscriptable):
    __slots__ = [column.name.lower() for column in Columns]
    __columns__ = Columns

    def write_json(self, file_name: str | Path) -> None:
        logger.info("write %i entries to file %s...", len(self), str(file_name))

        file = Path(file_name)
        file.write_text(self.to_json(), encoding="utf-8")

        logger.info("...done")

    @staticmethod
    def read_json(file_name: str | Path):
        logger.info("read from file %s...", str(file_name))

        file = Path(file_name)
        definition = json.loads(file.read_text(encoding="utf-8"))

        result = Comparable(definition)
        result.reset_index(drop=True, inplace=True)

        logger.info("...got %i entries", len(result))
        return result

    def write_csv(self, file_name: str | Path) -> None:
        file = Path(file_name)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)

        logger.info("prepare result data for output...")

        logger.info("write result to %s", str(file))
        file.write_text(self.to_csv(index=False), encoding="utf-8")
