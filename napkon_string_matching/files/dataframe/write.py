import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def write(file_path: str | Path, df: pd.DataFrame) -> None:
    """
    Write a `DataFrame` to file in JSON format

    Attributes
    ---
        file_path (str|Path):   file path to write to
        df (DataFrame):         DataFrame to write
    """

    logger.info("write %i entries to file %s...", len(df), str(file_path))

    file = Path(file_path)
    content = df.to_json()
    file.write_text(content)

    logger.info("...done")
