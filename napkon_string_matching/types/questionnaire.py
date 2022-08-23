import enum
import json
import logging
import warnings
from hashlib import md5
from pathlib import Path
from typing import List

import napkon_string_matching
import napkon_string_matching.types.comparable as comp
import numpy as np
import pandas as pd
from napkon_string_matching.types.comparable import Comparable
from napkon_string_matching.types.subscriptable import Subscriptable
from tqdm import tqdm


class Columns(enum.Enum):
    ITEM = "Item"
    SHEET = "Sheet"
    FILE = "File"
    CATEGORIES = "Categories"
    QUESTION = "Question"
    OPTIONS = "Options"
    TERM = "Term"
    TOKENS = "Tokens"
    TOKEN_IDS = "TokenIds"
    TOKEN_MATCH = "TokenMatch"
    IDENTIFIER = "Identifier"
    MATCHES = "Matches"
    VARIABLE = "Variable"


DATASETTABLE_COLUMN_DB_COLUMN = "Datenbankspalte"
DATASETTABLE_COLUMN_FILE = "FileName"
DATASETTABLE_COLUMN_ITEM = "Item"
DATASETTABLE_COLUMN_OPTIONS = "Optionen (durch Semikolons getrennt), Lookuptabelle"
DATASETTABLE_COLUMN_PROJECT = "Projekt"
DATASETTABLE_COLUMN_QUESTION = "Frage"
DATASETTABLE_COLUMN_NUMBER = "Nr."
DATASETTABLE_COLUMN_SHEET_NAME = "SheetName"
DATASETTABLE_COLUMN_TYPE = "Fragetyp (Konfiguration)"
DATASETTABLE_COLUMN_VARIABLE = "Datenbankspalte"

DATASETTABLE_TYPE_GROUP_DEFAULT = "StandardGroup"
DATASETTABLE_TYPE_GROUP_HORIZONAL = "HorizontalGroup"
DATASETTABLE_TYPE_HEADER = "Headline"

COLUMN_TEMP_SUBCATEGORY = "Subcategory"

DATASETTABLE_ITEM_SKIPABLE = "<->"

SUFFIX_LEFT = "_left"
SUFFIX_RIGHT = "_right"

COLUMN_SCORE = "Score"

CACHE_FILE_PATTERN = "compared/cache_score_{}.json"

SUFFIX_LEFT = "_left"
SUFFIX_RIGHT = "_right"

COLUMN_SCORE = "Score"

CACHE_FILE_PATTERN = "compared/cache_score_{}.json"

logger = logging.getLogger(__name__)


class Questionnaire(Subscriptable):
    __slots__ = [column.name.lower() for column in Columns]
    __columns__ = Columns

    def concat(self, others: List):
        if len(others) == 0:
            return self

        if not isinstance(others[0], Questionnaire):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(others[0]).__name__
                )
            )

        return Questionnaire(
            pd.concat([self._data, *[other._data for other in others]], ignore_index=True)
        )

    @staticmethod
    def read_json(file: str | Path):
        """
        Read a `Questionnaire` stored as JSON from file

        Attributes
        ---
            file_path (str|Path):   file path to read from

        Returns
        ---
            Questionnaire:  from the file contents
        """

        logger.info("read from file %s...", str(file))

        file = Path(file)
        definition = json.loads(file.read_text(encoding="utf-8"))

        result = Questionnaire(definition)
        result.reset_index(drop=True, inplace=True)

        logger.info("...got %i entries", len(result))
        return result

    def write_json(self, file: str | Path) -> None:
        """
        Write a `Questionnaire` to file in JSON format

        Attributes
        ---
            file_path (str|Path):   file path to write to
        """

        logger.info("write %i entries to file %s...", len(self), str(file))

        file = Path(file)
        file.write_text(self.to_json(), encoding="utf-8")

        logger.info("...done")

    @staticmethod
    def read_dataset_table(file: str | Path, *args, **kwargs):
        """
        Read a xlsx file

        The contents are returned as a list of dictionaries containing the row contents
        and meta information.

        attr
        ---
            xlsx_file (str|Path): file to read

        returns
        ---
            Questionnaire: parsed result
        """

        logger.info("read from file %s...", str(file))

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            file = pd.ExcelFile(file, engine="openpyxl")
        sheet_names = file.sheet_names[2:]

        logger.info("...reading %i sheets...", len(sheet_names))

        parser = SheetParser()
        sheets = []
        for sheet_name in sheet_names:
            data_list = parser.parse(file, sheet_name, *args, **kwargs)
            if data_list is not None:
                sheets.append(data_list)

        if not sheets:
            logger.warn("...dit not get any entries")
            return None

        result = Questionnaire().concat(sheets)

        logger.info("...got %i entries", len(result))

        return result

    def hash(self) -> str:
        return gen_hash(self._data.to_csv())

    def _hash_compare_args(self, other, *args, **kwargs) -> str:
        hashes = [self.hash(), other.hash()]

        hashes += [gen_hash(str(arg)) for arg in args]
        hashes += [gen_hash(str(kwargs)) for kwargs in kwargs.items()]

        return "".join(hashes)

    def compare(
        self,
        other,
        score_threshold: float = 0.1,
        compare_column: str = Columns.TOKEN_IDS,
        cached: bool = True,
        cache_threshold: float = None,
        *args,
        **kwargs,
    ) -> Comparable:

        # Get the compare dataframe that holds the score to match all entries from
        # the left with each from right dataset
        df_hash = self._hash_compare_args(other, *args, **kwargs)
        cache_score_file = Path(CACHE_FILE_PATTERN.format(df_hash))
        logger.debug("cache hash %s", df_hash)

        if cache_score_file.exists() and cached:
            logger.info("using cached result")
            result = Comparable.read_json(cache_score_file)
        else:
            if not cache_threshold:
                cache_threshold = score_threshold
            result = self._gen_comparable(
                other,
                score_threshold=cache_threshold,
                compare_column=compare_column,
                *args,
                **kwargs,
            )

            if not cache_score_file.parent.exists():
                cache_score_file.parent.mkdir(parents=True)

            logger.info("write cache to file")
            result.write_json(cache_score_file)

        # Filter outside of the caching to reuse same cache with different thresholds
        result = result[result.match_score >= score_threshold]
        logger.debug("got %i filtered entries", len(result))

        return result

    def _gen_comparable(
        self,
        right,
        score_func: str,
        score_threshold: float = 0.1,
        compare_column: str = Columns.TOKEN_IDS.value,
        *args,
        **kwargs,
    ) -> Comparable:
        score_func = getattr(napkon_string_matching.compare.score_functions, score_func)

        left = self.dropna(subset=[compare_column])
        right = right.dropna(subset=[compare_column])

        column_mapping = {Columns.QUESTION.value: comp.Columns.PARAMETER.value}
        left.rename(columns=column_mapping, inplace=True)
        right.rename(columns=column_mapping, inplace=True)

        right = right.add_prefix("Match")
        compare_df = left.merge(right, how="cross").dataframe()

        logger.info("calculate score")
        comparable = Comparable(compare_df)

        comparable.match_score = [
            score_func(param, match_param)
            for param, match_param in tqdm(
                zip(comparable[compare_column], comparable["Match" + compare_column]),
                total=len(comparable),
            )
        ]

        # Remove not needed columns
        comparable.drop_superfluous_columns()

        comparable = comparable[comparable.match_score >= score_threshold]
        logger.debug("got %i entries", len(comparable))

        return comparable


class SheetParser:
    """
    A parser for sheets of a dataset table
    """

    def __init__(self) -> None:
        self.current_categories = []
        self.current_question = None

    def parse(
        self,
        file: pd.ExcelFile,
        sheet_name: str,
        *args,
        **kwargs,
    ) -> Questionnaire:
        """
        Parses a single sheet

        Extracts meta information and information needed for matching
        and returns them as a list

        attr
        ---
            file (Excelfile): opened excel file
            sheet_name (str): name of the sheet to parse

        returns
        ---
            List[dict]: list of dictionary per line
        """
        self.current_categories = []
        self.current_question = None

        sheet: pd.DataFrame = pd.read_excel(
            file, sheet_name=sheet_name, na_values=DATASETTABLE_ITEM_SKIPABLE
        )

        # Remove leading meta information block on sheet
        start_index = np.where(sheet[DATASETTABLE_COLUMN_PROJECT] == DATASETTABLE_COLUMN_NUMBER)[0][
            0
        ]
        sheet.columns = sheet.iloc[start_index]
        sheet = sheet.iloc[start_index + 1 :, :].reset_index(drop=True)

        # Replace `NaN` with `None` for easier handling
        sheet.where(pd.notnull(sheet), None, inplace=True)

        # Add meta information to each row
        sheet[DATASETTABLE_COLUMN_SHEET_NAME] = sheet_name
        sheet[DATASETTABLE_COLUMN_FILE] = Path(file.io).stem

        return self.parse_rows(sheet, *args, **kwargs)

    def parse_rows(
        self,
        sheet: pd.DataFrame,
        filter_column: str = None,
        filter_prefix: str = None,
        *args,
        **kwargs,
    ) -> Questionnaire | None:

        # Fill category and subcategory if available
        sheet[Columns.CATEGORIES.value] = [
            question if type_ == DATASETTABLE_TYPE_HEADER else None
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
        ]
        sheet[COLUMN_TEMP_SUBCATEGORY] = [
            question
            if pd.notna(type_)
            and type_ != DATASETTABLE_TYPE_HEADER
            and all(entry not in type_ for entry in ["Group", "Matrix"])
            else None
            for question, type_ in zip(
                sheet[DATASETTABLE_COLUMN_QUESTION], sheet[DATASETTABLE_COLUMN_TYPE]
            )
        ]

        # Fill for all items category and subcategory if they belong to one
        sheet[Columns.CATEGORIES.value] = sheet[Columns.CATEGORIES.value].ffill()
        sheet[COLUMN_TEMP_SUBCATEGORY] = _fill_subcategories(
            sheet[Columns.CATEGORIES.value], sheet[COLUMN_TEMP_SUBCATEGORY]
        )

        # Combine both information in a single column
        sheet[Columns.CATEGORIES.value] = [
            _combine_categories(category, sub)
            for category, sub in zip(
                sheet[Columns.CATEGORIES.value], sheet[COLUMN_TEMP_SUBCATEGORY]
            )
        ]
        sheet.drop(columns=COLUMN_TEMP_SUBCATEGORY, inplace=True)

        # Remove all entries without items and variable names
        sheet.dropna(subset=[DATASETTABLE_COLUMN_ITEM, DATASETTABLE_COLUMN_DB_COLUMN], inplace=True)

        # Fill down questions to sub-items
        sheet[DATASETTABLE_COLUMN_QUESTION] = sheet[DATASETTABLE_COLUMN_QUESTION].ffill()

        # Filter entries if filter provided
        if filter_column and filter_prefix:
            sheet.drop(
                sheet[
                    [
                        not entry.startswith(filter_prefix) if pd.notna(entry) else False
                        for entry in sheet[filter_column]
                    ]
                ].index,
                inplace=True,
            )

        # Rename columns
        mappings = {
            DATASETTABLE_COLUMN_ITEM: Columns.ITEM.value,
            DATASETTABLE_COLUMN_SHEET_NAME: Columns.SHEET.value,
            DATASETTABLE_COLUMN_FILE: Columns.FILE.value,
            DATASETTABLE_COLUMN_QUESTION: Columns.QUESTION.value,
            DATASETTABLE_COLUMN_VARIABLE: Columns.VARIABLE.value,
        }
        sheet.rename(columns=mappings, inplace=True)

        # Create identifier column
        sheet[Columns.IDENTIFIER.value] = [
            _generate_identifier(file, sheet, str(index))
            for file, sheet, index in zip(
                sheet[Columns.FILE.value], sheet[Columns.SHEET.value], sheet.index
            )
        ]

        # Set options
        options = sheet.get(DATASETTABLE_COLUMN_OPTIONS)
        sheet[Columns.OPTIONS.value] = (
            [_generate_options(options_) for options_ in options] if options is not None else None
        )

        result = Questionnaire(sheet)
        result.drop_superfluous_columns()

        return result


def _fill_subcategories(categories: pd.Series, subcategories: pd.Series) -> List:
    result = []
    for index, entry in enumerate(zip(categories, subcategories)):
        prev_cat = categories[index - 1] if index > 0 else -1
        prev_sub = result[index - 1] if index > 0 else -1
        cat, sub = entry

        if not sub and prev_sub and prev_cat == cat:
            result.append(prev_sub)
        else:
            result.append(sub)
    return result


def _generate_identifier(file: str, sheet: str, row_name: str) -> str:
    return "#".join([file, sheet, row_name]).replace(" ", "-")


def _generate_options(options: str) -> List[str] | None:
    return (
        options.replace(";", "\n").replace("\n\n", "\n").splitlines() if pd.notna(options) else None
    )


def _combine_categories(first: str, second: str) -> List[str]:
    result = []
    if pd.notna(first):
        result.append(first)
    if pd.notna(second):
        result.append(second)
    return result if result else None


def gen_hash(string: str) -> str:
    return md5(string.encode("utf-8"), usedforsecurity=False).hexdigest()
