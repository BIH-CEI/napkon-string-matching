import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ReadableJson:
    @classmethod
    def read_json(cls, file_name: str | Path, *args, **kwargs):
        """
        Read data stored as JSON from file

        Attributes
        ---
            file_path (str|Path):   file path to read from

        Returns
        ---
            Self:  from the file contents
        """

        logger.info("read %s from file %s...", cls.__name__, str(file_name))

        file = Path(file_name)
        definition = json.loads(file.read_text(encoding="utf-8"))

        result = cls(data=definition)

        logger.info("...got %i entries", len(result))
        return result
