"""
Module to handle reading of `Datensatztabelle` files
"""

import warnings
from pathlib import Path

import pandas as pd
from napkon_string_matching.files.dataset_table import sheet_parser


def read(xlsx_file: str | Path) -> pd.DataFrame:
    """
    Read a xlsx file

    The contents are returned as a list of dictionaries containing the row contents
    and meta information.

    attr
    ---
        xlsx_file (str|Path): file to read

    returns
    ---
        List[dict]: parsed result
    """

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        file = pd.ExcelFile(xlsx_file, engine="openpyxl")
    sheet_names = file.sheet_names[2:]

    parser = sheet_parser.SheetParser()
    sheets = []
    for sheet_name in sheet_names:
        data_list = parser.parse(file, sheet_name)
        sheets.append(data_list)

    result = pd.concat(sheets)

    # Reset to get a valid continous index at the end
    return result.reset_index(drop=True)
