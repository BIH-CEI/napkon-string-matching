from typing import List


def intersection_vs_union(left: List[str], right: List[str]) -> float:
    set_left = set(left)
    set_right = set(right)

    return len(set_left.intersection(set_right)) / len(set_left.union(set_right))
