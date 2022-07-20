from typing import List

import numpy as np
import pandas as pd
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


def gen_term(categories: List[str], question: str, item: str) -> str:
    term_parts = []

    if categories:
        term_parts += categories
    if question:
        term_parts.append(question)
    if item:
        term_parts.append(item)

    return " ".join(term_parts)
