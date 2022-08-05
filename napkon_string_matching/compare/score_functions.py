from typing import List

from rapidfuzz import fuzz


def intersection_vs_union(left: List[str], right: List[str]) -> float:
    set_left = set(left)
    set_right = set(right)

    return len(set_left.intersection(set_right)) / len(set_left.union(set_right))


def fuzzy_match(left: List[str], right: List[str]) -> float:
    left_term = " ".join(sorted(left, key=str.lower))
    right_term = " ".join(sorted(right, key=str.lower))

    return fuzz.QRatio(left_term, right_term) / 100
