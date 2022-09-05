# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from itertools import product
from pathlib import Path
from typing import Dict

from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults
from napkon_string_matching.types.comparable_data import ComparableData
from napkon_string_matching.types.gecco_definition import GeccoDefinition
from napkon_string_matching.types.questionnaire import Questionnaire

RESULTS_FILE_PATTERN = "output/result_{score_threshold}_{compare_column}_{score_func}.xlsx"

CONFIG_FIELD_PREPARE = "prepare"
CONFIG_FIELD_MATCHING = "matching"
CONFIG_FIELD_FILES = "files"
CONFIG_GECCO_FILES = "gecco_definitions"


logger = logging.getLogger(__name__)


def match(config: Dict) -> None:
    preparator = get_preparator(config[CONFIG_FIELD_PREPARE])

    datasets: Dict[str, ComparableData] = {}
    for file in config[CONFIG_GECCO_FILES]:
        name = Path(file).stem
        dataset = GeccoDefinition.prepare(file, preparator, **config[CONFIG_FIELD_MATCHING])

        if dataset is None:
            logger.warning("didn't get any data")
            continue

        datasets[name] = dataset

    for file in config[CONFIG_FIELD_FILES]:
        name = Path(file).stem
        dataset = Questionnaire.prepare(file, preparator, **config[CONFIG_FIELD_MATCHING])

        if dataset is None:
            logger.warning("didn't get any data")
            continue

        datasets[name] = dataset

    comparisons = ComparisonResults()
    matched = set()
    for entry_left, entry_right in product(datasets.items(), datasets.items()):
        # Sort key entries to prevent processing of entries in both orders
        # e.g. 1 and 2 but not 2 and 1
        sorted_entries = tuple(sorted([entry_left, entry_right], key=lambda tup: tup[0].lower()))
        entry_first, entry_second = sorted_entries

        name_first, dataset_first = entry_first
        name_second, dataset_second = entry_second

        if name_first == name_second:
            continue

        key = tuple(sorted([name_first, name_second], key=str.lower))
        if key not in matched:
            matched.add(key)
            logger.info("compare %s and %s", name_first, name_second)
            matches = dataset_first.compare(dataset_second, **config[CONFIG_FIELD_MATCHING])
            comparisons[f"{name_first} vs {name_second}"] = matches

    analysis = _analyse(comparisons)
    _print_analysis(analysis)

    # write result
    format_args = {
        **config[CONFIG_FIELD_MATCHING],
        "score_func": config[CONFIG_FIELD_MATCHING]["score_func"].replace("_", "-"),
    }
    comparisons.write_excel(RESULTS_FILE_PATTERN.format(**format_args))


def get_preparator(config):
    return MatchPreparator(config)


def _analyse(results: ComparisonResults) -> Dict[str, Dict[str, str]]:
    """
    Analyses how many entries there are in the result and how many are matched.
    Also calcualtes these for all entries starting with the `gec_` prefix.
    """
    GECCO_PREFIX = "gec_"

    result = {}
    for name, comp in results.items():
        gecco_entries = comp[[GECCO_PREFIX in entry for entry in comp.variable]]
        gecco_match_entries = comp[[GECCO_PREFIX in entry for entry in comp.match_variable]]

        comp_result = {
            "matched": "{}/{}".format(comp.variable.nunique(), comp.match_variable.nunique()),
            "gecco": "{}/{}".format(
                gecco_entries.variable.nunique(), gecco_match_entries.match_variable.nunique()
            ),
        }
        result[name] = comp_result
    return result


def _print_analysis(analysis: Dict[str, Dict[str, str]]) -> None:
    for name, item in analysis.items():
        entries = []
        for key, value in item.items():
            entries.append("{}: {}".format(key, value))
        logger.info("%s\t%s", name, "\t".join(entries))
