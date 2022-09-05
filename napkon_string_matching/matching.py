# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from typing import Dict

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults

RESULTS_FILE_PATTERN = "output/result_{score_threshold}_{compare_column}_{score_func}.xlsx"

CONFIG_FIELD_PREPARE = "prepare"
CONFIG_FIELD_MATCHING = "matching"


logger = logging.getLogger(__name__)


def match(config: Dict) -> None:
    preparator = get_preparator(config[CONFIG_FIELD_PREPARE])
    matcher = Matcher(preparator, config)

    comparisons_parts = [
        matcher.match_gecco_with_questionnaires(),
        matcher.match_questionnaires(),
    ]

    comparisons = ComparisonResults()
    for comparison in comparisons_parts:
        comparisons.results.update(comparison.results)

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
