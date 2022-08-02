import logging
from hashlib import md5
from itertools import product
from pathlib import Path
from typing import List

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_IDENTIFIER,
    DATA_COLUMN_TOKEN_IDS,
)
from napkon_string_matching.files import dataframe
from tqdm import tqdm

logger = logging.getLogger(__name__)

SUFFIX_LEFT = "_left"
SUFFIX_RIGHT = "_right"

COMPARE_COLUMN = DATA_COLUMN_TOKEN_IDS


def _hash_dataframes(*dfs) -> str:
    return "_".join(
        [
            md5(df.to_csv().encode("utf-8"), usedforsecurity=False).hexdigest()
            for df in dfs
        ]
    )


def compare(dataset_left: pd.DataFrame, dataset_right: pd.DataFrame):

    df_hash = _hash_dataframes(dataset_left, dataset_right)
    cache_score_file = Path("compared") / ("cache_score_" + df_hash + ".json")

    # Get the compare dataframe that holds the score to match all entries from
    # the left with each from right dataset
    if cache_score_file.exists():
        compare_df = _read_compare_dataframe(cache_score_file)
    else:
        compare_df = _gen_compare_dataframe(
            dataset_left, dataset_right, cache_score_file
        )


def _read_compare_dataframe(cache_file: Path) -> pd.DataFrame:
    logger.info("using cached score")
    logger.debug("reading from %s", cache_file)
    compare_df = dataframe.read(cache_file)
    logger.debug("got %i entries", len(compare_df))
    return compare_df


def _gen_compare_dataframe(
    df_left: pd.DataFrame, df_right: pd.DataFrame, cache_file: Path
) -> pd.DataFrame:
    df1_filtered = _get_na_filtered(df_left, column=COMPARE_COLUMN)
    df2_filtered = _get_na_filtered(df_right, column=COMPARE_COLUMN)

    compare_df = _gen_permutation(
        df1_filtered,
        df2_filtered,
        columns=[DATA_COLUMN_IDENTIFIER, COMPARE_COLUMN],
        suffix_left=SUFFIX_LEFT,
        suffix_right=SUFFIX_RIGHT,
    )

    logger.info("calculate score")
    compare_df["Score"] = [
        _calc_score(row, SUFFIX_LEFT, SUFFIX_RIGHT)
        for _, row in tqdm(compare_df.iterrows(), total=len(compare_df))
    ]

    compare_df = compare_df[compare_df["Score"] > 0]
    logger.debug("got %i entries", len(compare_df))

    if not cache_file.parent.exists():
        cache_file.parent.mkdir(parents=True)

    logger.info("write cache to file")
    logger.debug("write to %s", cache_file)
    dataframe.write(cache_file, compare_df)

    return compare_df


def _get_na_filtered(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.dropna(subset=[column]).reset_index(drop=True)


def _gen_permutation(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    columns: List[str],
    suffix_left: str,
    suffix_right: str,
) -> pd.DataFrame:
    IDX_LEFT = "idx" + suffix_left
    IDX_RIGHT = "idx" + suffix_right

    join_df = pd.DataFrame(
        product(df_left.index, df_right.index), columns=[IDX_LEFT, IDX_RIGHT]
    )

    permutation = _merge_df(
        _merge_df(
            join_df, df_left, columns, left_on=IDX_LEFT, suffix_right=suffix_left
        ),
        df_right,
        columns,
        left_on=IDX_RIGHT,
        suffix_right=suffix_right,
    )

    permutation.drop(columns=[IDX_LEFT, IDX_RIGHT], inplace=True)

    return permutation


def _merge_df(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    columns: List[str],
    left_on: str,
    suffix_right: str,
) -> pd.DataFrame:
    return df1.merge(
        df2[columns].add_suffix(suffix_right), left_on=left_on, right_index=True
    )


def _calc_score(row: pd.Series, suffix_left: str, suffix_right: str) -> float:
    INSPECT_COLUMN = DATA_COLUMN_TOKEN_IDS

    INSPECT_COLUMN_LEFT = INSPECT_COLUMN + suffix_left
    INSPECT_COLUMN_RIGHT = INSPECT_COLUMN + suffix_right

    set_left = set(row[INSPECT_COLUMN_LEFT])
    set_right = set(row[INSPECT_COLUMN_RIGHT])

    return len(set_left.intersection(set_right)) / len(set_left.union(set_right))
