from pathlib import Path

import pandas as pd


def write(file_path: str | Path, df: pd.DataFrame) -> None:
    """
    Write a `DataFrame` to file in JSON format

    Attributes
    ---
        file_path (str|Path):   file path to write to
        df (DataFrame):         DataFrame to write
    """

    file = Path(file_path)
    content = df.to_json()
    file.write_text(content)
