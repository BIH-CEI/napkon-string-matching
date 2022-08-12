import json
import logging
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import DATA_COLUMN_IDENTIFIER

logger = logging.getLogger(__name__)


def read(file_path: str | Path) -> pd.DataFrame:
    """
    Read a `DataFrame` stored as JSON from file

    Attributes
    ---
        file_path (str|Path):   file path to read from

    Returns
    ---
        DataFrame:  from the file contents
    """

    logger.info("read from file %s...", str(file_path))

    file = Path(file_path)
    content = json.loads(file.read_text())

    df = pd.DataFrame.from_dict(content)
    df.index.name = DATA_COLUMN_IDENTIFIER

    logger.info("...got %i entries", len(df))
    return df


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
