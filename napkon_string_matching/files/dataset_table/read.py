"""
Module to handle reading of `Datensatztabelle` files
"""

import logging
import warnings
from pathlib import Path

import pandas as pd
from napkon_string_matching.constants import DATA_COLUMN_IDENTIFIER
from napkon_string_matching.files.dataset_table import sheet_parser

logger = logging.getLogger(__name__)


def read(xlsx_file: str | Path, *args, **kwargs) -> pd.DataFrame:
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

    logger.info("read from file %s...", str(xlsx_file))

    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        file = pd.ExcelFile(xlsx_file, engine="openpyxl")
    sheet_names = file.sheet_names[2:]

    logger.info("...reading %i sheets...", len(sheet_names))

    parser = sheet_parser.SheetParser()
    sheets = []
    for sheet_name in sheet_names:
        data_list = parser.parse(file, sheet_name, *args, **kwargs)
        if data_list is not None:
            sheets.append(data_list)

    if not sheets:
        logger.warn("...dit not get any entries")
        return None

    result = pd.concat(sheets)

    # Reset to get a valid continous index at the end
    result.set_index(DATA_COLUMN_IDENTIFIER, inplace=True)

    logger.info("...got %i entries", len(result))

    return result
