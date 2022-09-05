import logging
from itertools import product
from typing import Dict

from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults
from napkon_string_matching.types.gecco_definition import GeccoDefinition
from napkon_string_matching.types.questionnaire import Questionnaire

CONFIG_GECCO_FILES = "gecco_definition"
CONFIG_FIELD_FILES = "files"
CONFIG_FIELD_MATCHING = "matching"

logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, preparator: MatchPreparator, config: Dict) -> None:
        self.preparator = preparator
        self.config = config
        self.gecco: GeccoDefinition = None
        self.questionnaires: Dict[str, Questionnaire] = None

        self._init_gecco_definition()
        self._init_questionnaires()

    def _init_gecco_definition(self) -> None:
        file: str | None = self.config.get(CONFIG_GECCO_FILES)
        self.gecco = GeccoDefinition.prepare(
            file, self.preparator, **self.config[CONFIG_FIELD_MATCHING]
        )

        if self.gecco is None:
            logger.warning("didn't get any data")

    def _init_questionnaires(self) -> None:
        self.questionnaires = {}
        for name, file in self.config[CONFIG_FIELD_FILES].items():
            dataset = Questionnaire.prepare(
                file, self.preparator, **self.config[CONFIG_FIELD_MATCHING]
            )

            if dataset is None:
                logger.warning("didn't get any data")
                continue
            else:
                self.questionnaires[name] = dataset

    def match_gecco_with_questionnaires(self) -> ComparisonResults:
        comparisons = ComparisonResults()
        for name, questionnaire in self.questionnaires.items():
            logger.info("compare gecco and %s", name)
            matches = self.gecco.compare(questionnaire, **self.config[CONFIG_FIELD_MATCHING])
            comparisons[f"gecco vs {name}"] = matches
        return comparisons

    def match_questionnaires(self) -> ComparisonResults:
        comparisons = ComparisonResults()
        matched = set()
        for entry_left, entry_right in product(
            self.questionnaires.items(), self.questionnaires.items()
        ):
            # Sort key entries to prevent processing of entries in both orders
            # e.g. 1 and 2 but not 2 and 1
            sorted_entries = tuple(
                sorted([entry_left, entry_right], key=lambda tup: tup[0].lower())
            )
            entry_first, entry_second = sorted_entries

            name_first, dataset_first = entry_first
            name_second, dataset_second = entry_second

            if name_first == name_second:
                continue

            key = tuple(sorted([name_first, name_second], key=str.lower))
            if key not in matched:
                matched.add(key)
                logger.info("compare %s and %s", name_first, name_second)
                matches = dataset_first.compare(
                    dataset_second, **self.config[CONFIG_FIELD_MATCHING]
                )
                comparisons[f"{name_first} vs {name_second}"] = matches
        return comparisons
