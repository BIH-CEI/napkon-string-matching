from typing import Dict, List, Tuple

import nltk
import numpy as np
import pandas as pd
from rapidfuzz import fuzz

nltk.download("punkt")
nltk.download("stopwords")

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def gen_tokens(
    term: str, reference: pd.DataFrame, headings: pd.DataFrame, score_threshold: int
) -> Tuple[List[str], List[str], Dict[str, str]]:
    """
    Generate tokens from term, references and headings

    Returns
    ---
        Tuple[List[str], List[str], Dict[str, str]]: Tuple of headings, ids and the complete match information
    """
    ref_copy = reference.copy(deep=True)

    ref_copy["score"] = np.vectorize(fuzz.WRatio)(ref_copy["term"], term)

    # Get IDs above threshold
    ref_copy = ref_copy[ref_copy["score"] >= score_threshold].drop_duplicates(
        subset="id"
    )

    # Get the corsponding headings
    ref_copy = ref_copy.merge(headings, on="id", suffixes=(None, "_heading"))

    return (
        list(ref_copy["term_heading"].values),
        list(ref_copy["id"].values),
        list(ref_copy.values),
    )


def gen_term(
    categories: List[str], question: str, item: str, language: str = "german"
) -> str:
    term_parts = []

    if categories:
        term_parts += categories
    if question:
        term_parts.append(question)
    if item:
        term_parts.append(item)

    tokens = word_tokenize(" ".join(term_parts))

    stop_words = set(stopwords.words(language))
    tokens = [word for word in tokens if word.casefold() not in stop_words]

    return " ".join(tokens)
