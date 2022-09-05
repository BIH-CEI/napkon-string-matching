# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from typing import Dict

from napkon_string_matching.matcher import Matcher
from napkon_string_matching.prepare.match_preparator import MatchPreparator

CONFIG_FIELD_PREPARE = "prepare"
CONFIG_FIELD_MATCHING = "matching"


logger = logging.getLogger(__name__)


def match(config: Dict) -> None:
    preparator = MatchPreparator(config[CONFIG_FIELD_PREPARE])
    matcher = Matcher(preparator, config)

    matcher.match_questionnaires_variables()
    matcher.match_gecco_with_questionnaires()
    matcher.match_questionnaires()

    matcher.print_analysis()

    matcher.write_results()
