from typing import Dict, List, Tuple

import nltk
import numpy as np
import pandas as pd
from napkon_string_matching.terminology.mesh.constants import (
    TERMINOLOGY_COLUMN_ID,
    TERMINOLOGY_COLUMN_TERM,
)
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from rapidfuzz import fuzz

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"
PREPARE_COLUMN_SCORE = "Score"


def gen_tokens(
    term: List[str],
    reference: pd.DataFrame,
    headings: pd.DataFrame,
    score_threshold: int,
) -> Tuple[List[str], List[str], Dict[str, str]]:
    """
    Generate tokens from term, references and headings

    Returns
    ---
        Tuple[List[str], List[str], Dict[str, str]]: Tuple of headings,
        ids and the complete match information
    """
    ref_copy = reference.copy(deep=True)

    # Calculate the score for each combination
    term_str = " ".join(term)
    ref_copy[PREPARE_COLUMN_SCORE] = np.vectorize(fuzz.WRatio)(
        ref_copy[TERMINOLOGY_COLUMN_TERM], term_str
    )

    # Get IDs above threshold
    ref_copy = ref_copy[ref_copy[PREPARE_COLUMN_SCORE] >= score_threshold].drop_duplicates(
        subset=TERMINOLOGY_COLUMN_ID
    )

    # Get the corsponding headings
    ref_copy = ref_copy.merge(headings, on=TERMINOLOGY_COLUMN_ID, suffixes=(None, "_heading"))

    return (
        list(ref_copy["Term_heading"].values),
        list(ref_copy[TERMINOLOGY_COLUMN_ID].values),
        list(ref_copy.values),
    )


def gen_term(categories: List[str], question: str, item: str, language: str = "german") -> str:
    term_parts = []

    if categories:
        term_parts += categories
    if question:
        term_parts.append(question)
    if item:
        term_parts.append(item)

    tokens = word_tokenize(" ".join(term_parts))

    stop_words = set(stopwords.words(language))
    tokens = {
        word
        for word in tokens
        if word.casefold() not in stop_words and word not in PREPARE_REMOVE_SYMBOLS
    }

    return sorted(tokens, key=str.casefold)
