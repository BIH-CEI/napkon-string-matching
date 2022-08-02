import logging
from hashlib import md5
from itertools import product
from pathlib import Path
from typing import List

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_IDENTIFIER,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_MATCHES,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_TOKEN_IDS,
)
from napkon_string_matching.files import dataframe
from tqdm import tqdm

logger = logging.getLogger(__name__)

SUFFIX_LEFT = "_left"
SUFFIX_RIGHT = "_right"

COLUMN_COMPARE = DATA_COLUMN_TOKEN_IDS
COLUMN_SCORE = "Score"


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

    _enhance_dataset_with_matches(
        dataset=dataset_left,
        column_suffix=SUFFIX_LEFT,
        other=dataset_right,
        other_suffix=SUFFIX_RIGHT,
        matches=compare_df,
    )
    _enhance_dataset_with_matches(
        dataset=dataset_right,
        column_suffix=SUFFIX_RIGHT,
        other=dataset_left,
        other_suffix=SUFFIX_LEFT,
        matches=compare_df,
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
    df1_filtered = _get_na_filtered(df_left, column=COLUMN_COMPARE)
    df2_filtered = _get_na_filtered(df_right, column=COLUMN_COMPARE)

    compare_df = _gen_permutation(df1_filtered, df2_filtered)

    logger.info("calculate score")
    compare_df[COLUMN_SCORE] = [
        _calc_score(row)
        for _, row in tqdm(compare_df.iterrows(), total=len(compare_df))
    ]

    compare_df = compare_df[compare_df[COLUMN_SCORE] > 0]
    logger.debug("got %i entries", len(compare_df))

    if not cache_file.parent.exists():
        cache_file.parent.mkdir(parents=True)

    logger.info("write cache to file")
    logger.debug("write to %s", cache_file)
    dataframe.write(cache_file, compare_df)

    return compare_df


def _get_na_filtered(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.dropna(subset=[column])


def _gen_permutation(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
) -> pd.DataFrame:
    IDX_LEFT = DATA_COLUMN_IDENTIFIER + SUFFIX_LEFT
    IDX_RIGHT = DATA_COLUMN_IDENTIFIER + SUFFIX_RIGHT

    join_df = pd.DataFrame(
        product(df_left.index, df_right.index), columns=[IDX_LEFT, IDX_RIGHT]
    )

    # Merge the product of both indices with their dataframes
    permutation = _merge_df(
        _merge_df(join_df, df_left, left_on=IDX_LEFT, suffix_right=SUFFIX_LEFT),
        df_right,
        left_on=IDX_RIGHT,
        suffix_right=SUFFIX_RIGHT,
    )

    return permutation


def _merge_df(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    left_on: str,
    suffix_right: str,
) -> pd.DataFrame:
    return df1.merge(
        df2[[COLUMN_COMPARE]].add_suffix(suffix_right),
        left_on=left_on,
        right_index=True,
    )


def _calc_score(row: pd.Series) -> float:
    INSPECT_COLUMN = DATA_COLUMN_TOKEN_IDS

    INSPECT_COLUMN_LEFT = INSPECT_COLUMN + SUFFIX_LEFT
    INSPECT_COLUMN_RIGHT = INSPECT_COLUMN + SUFFIX_RIGHT

    set_left = set(row[INSPECT_COLUMN_LEFT])
    set_right = set(row[INSPECT_COLUMN_RIGHT])

    return len(set_left.intersection(set_right)) / len(set_left.union(set_right))


def _enhance_dataset_with_matches(
    dataset: pd.DataFrame,
    column_suffix: str,
    other: pd.DataFrame,
    other_suffix: str,
    matches: pd.DataFrame,
) -> None:
    group_column = DATA_COLUMN_IDENTIFIER + column_suffix
    other_column = DATA_COLUMN_IDENTIFIER + other_suffix

    other_filtered = other[
        [
            DATA_COLUMN_CATEGORIES,
            DATA_COLUMN_QUESTION,
            DATA_COLUMN_ITEM,
        ]
    ]

    grouping = matches.groupby(by=group_column)
    for identifier in grouping.groups:
        match_information = grouping.get_group(identifier)

        # Get entries from `other` that where matched
        matched_entries = match_information.merge(
            other_filtered,
            how="left",
            left_on=other_column,
            right_on=DATA_COLUMN_IDENTIFIER,
        )

        match = [
            (
                score,
                identifier,
                (f"{','.join(categories)}:" if categories else "")
                + f"{question}:{item}",
            )
            for score, identifier, categories, question, item in zip(
                matched_entries[COLUMN_SCORE],
                matched_entries[other_column],
                matched_entries[DATA_COLUMN_CATEGORIES],
                matched_entries[DATA_COLUMN_QUESTION],
                matched_entries[DATA_COLUMN_ITEM],
            )
        ]

        if DATA_COLUMN_MATCHES not in dataset:
            dataset[DATA_COLUMN_MATCHES] = None

        # Get previous matches, get `None` if column does not exist
        previous = dataset.loc[identifier, DATA_COLUMN_MATCHES]

        # If cell did not include any values before, initialize with empty list for consistent
        # adding of new entries
        if not previous:
            previous = []

        dataset.at[identifier, DATA_COLUMN_MATCHES] = previous + match
