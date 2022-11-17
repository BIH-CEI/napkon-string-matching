from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.types.comparable_data import Columns
from napkon_string_matching.types.dataset_table.dataset_table import DatasetTable
from napkon_string_matching.types.mapping import Mapping


def get_all_table_subgroup_name_combinations(dataset_tables: Dict[str, DatasetTable]):
    """
    Get a dictionary containing all subgroups and their groups a human readable name
    for each DatasetTable.
    """
    result = {}
    for name, dataset_table in dataset_tables.items():
        result[name] = {}
        for group, subgroups in dataset_table.subgroups.items():
            result[name][dataset_table.groups[group]] = [
                dataset_table.subgroup_names[subgroup] for subgroup in subgroups
            ]
    return result


def get_match_result_table(
    matcher: Matcher, mappings_file: str | Path, left_name: str, right_name: str
):
    mapping = Mapping.read_json(mappings_file)
    combined = _generate_combinations(mapping, left_name, right_name)
    return generate_result_table(matcher, combined, left_name, right_name)


def _generate_combinations(mapping: Mapping, left_name: str, right_name: str):
    combined: List[Tuple[str, str]] = list(mapping[left_name][right_name]._data.items())
    combined2: List[Tuple[str, str]] = [
        (left, right) for right, left in mapping[right_name][left_name]._data.items()
    ]
    result = pd.DataFrame(combined + combined2)
    return result.drop_duplicates()


def get_oneunique_match_result_table(
    matcher: Matcher, mappings_file: str | Path, left_name: str, right_name: str
):
    mapping = Mapping.read_json(mappings_file)
    combined = _generate_combinations(mapping, left_name, right_name)

    result1 = combined.drop_duplicates(subset=0, keep=False)
    result2 = combined.drop_duplicates(subset=1, keep=False)
    combined = result1.merge(result2, on=[0, 1])

    return generate_result_table(matcher, combined, left_name, right_name)


def generate_result_table(matcher: Matcher, matches: pd.DataFrame, left_name: str, right_name: str):
    left = matcher.questionnaires[left_name]
    right = matcher.questionnaires[right_name]

    columns = [Columns.IDENTIFIER.value, Columns.SHEET.value, Columns.PARAMETER.value]
    left = left[columns]
    right = right[columns]

    left = left.add_prefix(left_name.title())
    right = right.add_prefix(right_name.title())
    left_id = left_name.title() + Columns.IDENTIFIER.value
    right_id = right_name.title() + Columns.IDENTIFIER.value

    matches = matches.merge(
        left,
        left_on=0,
        right_on=left_id,
    )
    matches = matches.merge(
        right,
        left_on=1,
        right_on=right_id,
    )

    return matches.drop([0, 1], axis="columns")
