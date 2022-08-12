import logging
from hashlib import md5
from itertools import product
from pathlib import Path
from typing import Callable

import napkon_string_matching
import napkon_string_matching.compare.score_functions
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

SUFFIX_LEFT = "_left"
SUFFIX_RIGHT = "_right"

COLUMN_SCORE = "Score"

CACHE_FILE_PATTERN = "compared/cache_score_{}.json"


logger = logging.getLogger(__name__)


def compare(
    dataset_left: pd.DataFrame,
    dataset_right: pd.DataFrame,
    score_threshold: float = 0.1,
    compare_column: str = DATA_COLUMN_TOKEN_IDS,
    *args,
    **kwargs,
) -> pd.DataFrame:

    # Get the compare dataframe that holds the score to match all entries from
    # the left with each from right dataset
    compare_df = _gen_compare_dataframe_cached(
        dataset_left,
        dataset_right,
        score_threshold=score_threshold,
        compare_column=compare_column,
        *args,
        **kwargs,
    )

    return compare_df


def _gen_compare_dataframe_cached(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    score_threshold: float = 0.1,
    cache_threshold: float = None,
    *args,
    **kwargs,
) -> pd.DataFrame:
    df_hash = _hash_dataframes(dfs=[df_left, df_right], *args, **kwargs)
    cache_score_file = Path(CACHE_FILE_PATTERN.format(df_hash))
    logger.debug("cache hash %s", df_hash)

    if cache_score_file.exists():
        compare_df = _read_compare_dataframe(cache_score_file)
    else:
        if not cache_threshold:
            cache_threshold = score_threshold
        compare_df = _gen_compare_dataframe(
            df_left, df_right, score_threshold=cache_threshold, *args, **kwargs
        )

        if not cache_score_file.parent.exists():
            cache_score_file.parent.mkdir(parents=True)

        logger.info("write cache to file")
        dataframe.write(cache_score_file, compare_df)

    # Filter outside of the caching to reuse same cache with different thresholds
    compare_df = compare_df[compare_df[COLUMN_SCORE] >= score_threshold]
    logger.debug("got %i filtered entries", len(compare_df))

    return compare_df


def _hash_dataframes(dfs, *args, **kwargs) -> str:
    hashes = [md5(df.to_csv().encode("utf-8"), usedforsecurity=False).hexdigest() for df in dfs]

    hashes += [md5(str(arg).encode("utf-8"), usedforsecurity=False).hexdigest() for arg in args]
    hashes += [
        md5(str(kwargs).encode("utf-8"), usedforsecurity=False).hexdigest()
        for kwargs in kwargs.items()
    ]

    return "".join(hashes)


def _read_compare_dataframe(cache_file: Path) -> pd.DataFrame:
    logger.info("using cached score")
    logger.debug("reading from %s", cache_file)
    compare_df = dataframe.read(cache_file)
    logger.debug("got %i entries", len(compare_df))
    return compare_df


def _gen_compare_dataframe(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    score_func: str,
    score_threshold: float = 0.1,
    compare_column: str = DATA_COLUMN_TOKEN_IDS,
    *args,
    **kwargs,
) -> pd.DataFrame:
    score_func = getattr(napkon_string_matching.compare.score_functions, score_func)

    df1_filtered = _get_na_filtered(df_left, column=compare_column)
    df2_filtered = _get_na_filtered(df_right, column=compare_column)

    compare_df = _gen_permutation(df1_filtered, df2_filtered, compare_column=compare_column)

    logger.info("calculate score")
    compare_df[COLUMN_SCORE] = [
        _calc_score(score_func, row, compare_column=compare_column)
        for _, row in tqdm(compare_df.iterrows(), total=len(compare_df))
    ]

    compare_df = compare_df[compare_df[COLUMN_SCORE] >= score_threshold]
    logger.debug("got %i entries", len(compare_df))

    return compare_df


def _get_na_filtered(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df.dropna(subset=[column])


def _gen_permutation(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    compare_column: str,
) -> pd.DataFrame:
    IDX_LEFT = DATA_COLUMN_IDENTIFIER + SUFFIX_LEFT
    IDX_RIGHT = DATA_COLUMN_IDENTIFIER + SUFFIX_RIGHT

    join_df = pd.DataFrame(product(df_left.index, df_right.index), columns=[IDX_LEFT, IDX_RIGHT])

    # Merge the product of both indices with their dataframes
    permutation = _merge_df(
        _merge_df(
            join_df,
            df_left,
            left_on=IDX_LEFT,
            suffix_right=SUFFIX_LEFT,
            compare_column=compare_column,
        ),
        df_right,
        left_on=IDX_RIGHT,
        suffix_right=SUFFIX_RIGHT,
        compare_column=compare_column,
    )

    return permutation


def _merge_df(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    left_on: str,
    suffix_right: str,
    compare_column: str,
) -> pd.DataFrame:
    return df1.merge(
        df2[[compare_column]].add_suffix(suffix_right),
        left_on=left_on,
        right_index=True,
    )


def _calc_score(score_func: Callable, row: pd.Series, compare_column: str) -> float:
    INSPECT_COLUMN_LEFT = compare_column + SUFFIX_LEFT
    INSPECT_COLUMN_RIGHT = compare_column + SUFFIX_RIGHT

    return score_func(row[INSPECT_COLUMN_LEFT], row[INSPECT_COLUMN_RIGHT])


def enhance_datasets_with_matches(
    dataset_left: pd.DataFrame, dataset_right: pd.DataFrame, matches: pd.DataFrame
) -> None:
    _enhance_dataset_with_matches(
        dataset=dataset_left,
        column_suffix=SUFFIX_LEFT,
        other=dataset_right,
        other_suffix=SUFFIX_RIGHT,
        matches=matches,
    )
    _enhance_dataset_with_matches(
        dataset=dataset_right,
        column_suffix=SUFFIX_RIGHT,
        other=dataset_left,
        other_suffix=SUFFIX_LEFT,
        matches=matches,
    )


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

    logger.info("adding %i matches to dataframe...", len(matches))

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
                (f"{','.join(categories)}:" if categories else "") + f"{question}:{item}",
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

    logger.info("...done")
