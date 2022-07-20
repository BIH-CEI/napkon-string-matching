"""
Module to handle reading of `Datensatztabelle` files
"""

from typing import List

import pandas as pd
from napkon_string_matching.io.dataset_table import sheet_parser


def read(xlsx_file: str) -> List[dict]:
    """
    Read a xlsx file

    The contents are returned as a list of dictionaries containing the row contents
    and meta information.

    attr
    ---
        xlsx_file (str): file to read

    returns
    ---
        List[dict]: parsed result
    """
    file = pd.ExcelFile(xlsx_file)
    sheet_names = file.sheet_names[2:]

    parser = sheet_parser.SheetParser()
    data = []
    for sheet_name in sheet_names:
        data_list = parser.parse(file, sheet_name)
        data += data_list

    return data
