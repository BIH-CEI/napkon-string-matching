from itertools import product
from typing import List

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_IDENTIFIER,
    DATA_COLUMN_TOKEN_IDS,
)


def compare(dataset_left: pd.DataFrame, dataset_right: pd.DataFrame):
    SUFFIX_LEFT = "_left"
    SUFFIX_RIGHT = "_right"

    COMPARE_COLUMN = DATA_COLUMN_TOKEN_IDS

    df1_filtered = _get_na_filtered(dataset_left, column=COMPARE_COLUMN)
    df2_filtered = _get_na_filtered(dataset_right, column=COMPARE_COLUMN)

    compare_df = _gen_permutation(
        df1_filtered,
        df2_filtered,
        columns=[DATA_COLUMN_IDENTIFIER, COMPARE_COLUMN],
        suffix_left=SUFFIX_LEFT,
        suffix_right=SUFFIX_RIGHT,
    )


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
