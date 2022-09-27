import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WritableCsv:
    def write_csv(self, file_name: str | Path, *args, **kwargs) -> None:
        """
        Write data to file in JSON format

        Attributes
        ---
            file_path (str|Path):   file path to write to
        """

        logger.info("write %i entries to file %s...", len(self), str(file_name))

        file = Path(file_name)
        file.write_text(self.to_csv(), encoding="utf-8")

        logger.info("...done")

    def to_csv(self) -> str:
        raise NotImplementedError()
