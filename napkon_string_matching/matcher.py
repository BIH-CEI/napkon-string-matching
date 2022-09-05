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

RESULTS_FILE_PATTERN = "output/result_{score_threshold}_{compare_column}_{score_func}.xlsx"


logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, preparator: MatchPreparator, config: Dict) -> None:
        self.preparator = preparator
        self.config = config
        self.gecco: GeccoDefinition = None
        self.questionnaires: Dict[str, Questionnaire] = None
        self.results: ComparisonResults = None

        self._init_gecco_definition()
        self._init_questionnaires()
        self.clear_results()

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

    def clear_results(self) -> None:
        self.results = ComparisonResults()

    def match_gecco_with_questionnaires(self) -> None:
        for name, questionnaire in self.questionnaires.items():
            logger.info("compare gecco and %s", name)
            matches = self.gecco.compare(questionnaire, **self.config[CONFIG_FIELD_MATCHING])
            self.results[f"gecco vs {name}"] = matches

    def match_questionnaires(self, prefix: str = None, *args, **kwargs) -> None:
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
                    dataset_second, **{**self.config[CONFIG_FIELD_MATCHING], **kwargs}
                )
                self.results[f"{prefix if prefix else ''}{name_first} vs {name_second}"] = matches

    def match_questionnaires_variables(self) -> ComparisonResults:
        self.match_questionnaires(prefix="var_", compare_column="Variable", score_threshold=0.85)

    def print_analysis(self) -> None:
        analysis = self._analyse()
        Matcher._print_analysis(analysis)

    def _analyse(self) -> Dict[str, Dict[str, str]]:
        """
        Analyses how many entries there are in the result and how many are matched.
        Also calcualtes these for all entries starting with the `gec_` prefix.
        """
        GECCO_PREFIX = "gec_"

        result = {}
        for name, comp in self.results.items():
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

    @staticmethod
    def _print_analysis(analysis: Dict[str, Dict[str, str]]) -> None:
        for name, item in analysis.items():
            entries = []
            for key, value in item.items():
                entries.append("{}: {}".format(key, value))
            logger.info("%s\t%s", name, "\t".join(entries))

    def write_results(self) -> None:
        format_args = {
            **self.config[CONFIG_FIELD_MATCHING],
            "score_func": self.config[CONFIG_FIELD_MATCHING]["score_func"].replace("_", "-"),
        }
        self.results.write_excel(RESULTS_FILE_PATTERN.format(**format_args))
