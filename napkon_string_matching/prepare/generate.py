from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"


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
