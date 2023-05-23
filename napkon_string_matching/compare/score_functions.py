from typing import List

from rapidfuzz import fuzz


def intersection_vs_union(left: List[str] | str, right: List[str] | str) -> float:
    """
    Ratio between the intersection and union of the tokens in `left` and `right`.
    """
    set_left = set(left if isinstance(left, list) else left.split())
    set_right = set(right if isinstance(right, list) else right.split())

    return len(set_left.intersection(set_right)) / len(set_left.union(set_right))


def join_sorted(value: List[str]) -> str:
    return " ".join(sorted(value, key=str.lower))


def fuzzy_match(left: str | List[str], right: str | List[str]) -> float:
    """
    QRatio of the Levenshtein distance of the `left` and `right` terms.
    """
    left_term = join_sorted(left) if isinstance(left, list) else left
    right_term = join_sorted(right) if isinstance(right, list) else right

    return fuzz.QRatio(left_term, right_term) / 100
