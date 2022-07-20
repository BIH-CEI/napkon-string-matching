import numpy as np
import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_QUESTION,
)
from rapidfuzz import fuzz


def gen_token(
    term: str, reference: pd.DataFrame, headings: pd.DataFrame, score_threshold: int
):
    ref_copy = reference.copy(deep=True)

    ref_copy["score"] = np.vectorize(fuzz.WRatio)(ref_copy["term"], term)

    # Get IDs above threshold
    ref_copy = ref_copy[ref_copy["score"] >= score_threshold].drop_duplicates(
        subset="id"
    )

    # Get the corsponding headings
    ref_copy = ref_copy.merge(headings, on="id", suffixes=(None, "_heading"))

    result = {
        "terms": list(ref_copy["term_heading"].values),
        "ids": list(ref_copy["id"].values),
        "mesh": list(ref_copy.values),
    }

    return result


def gen_term(series: pd.Series) -> str:
    term_parts = []

    if entry := series.get(DATA_COLUMN_CATEGORIES, None):
        term_parts += entry
    if entry := series.get(DATA_COLUMN_QUESTION, None):
        term_parts.append(entry)
    if entry := series.get(DATA_COLUMN_ITEM, None):
        term_parts.append(entry)

    return " ".join(term_parts)
