# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from typing import Dict

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.prepare.match_preparator import MatchPreparator

CONFIG_FIELD_PREPARE = "prepare"
CONFIG_FIELD_MATCHING = "matching"
CONFIG_FIELD_STEPS = "steps"


logger = logging.getLogger(__name__)


def match(config: Dict, use_cache=True) -> None:
    matcher = create_matcher(config, use_cache)

    for step in config[CONFIG_FIELD_STEPS]:
        match step:
            case "variables":
                matcher.match_questionnaires_variables()
            case "gecco":
                matcher.match_gecco_with_questionnaires()
            case "questionnaires":
                matcher.match_questionnaires()

    matcher.print_analysis()

    matcher.write_results()


def create_matcher(config: Dict, use_cache=True):
    preparator = MatchPreparator(config[CONFIG_FIELD_PREPARE])
    matcher = Matcher(preparator, config, use_cache=use_cache)
    return matcher
