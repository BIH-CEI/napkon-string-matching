# `napkon_string_matching.compare` Module

List of functions to generate a score describing the two entries. Each function accepts two terms or lists of tokens:

```python
def intersection_vs_union(left: List[str] | str, right: List[str] | str) -> float
```

Ratio of same tokens of both terms ccompared to the total number of tokens.

```python
def fuzzy_match(left: str | List[str], right: str | List[str]) -> float
```

QRatio of fuzzy matching. Similar to Levenshtein distance
