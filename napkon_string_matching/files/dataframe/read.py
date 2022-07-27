import json
from pathlib import Path

import pandas as pd


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

    file = Path(file_path)
    content = json.loads(file.read_text())
    df = pd.DataFrame.from_dict(content)
    return df.reset_index(drop=True)
