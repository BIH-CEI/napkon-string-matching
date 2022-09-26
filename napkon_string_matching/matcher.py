import logging
from itertools import product
from pathlib import Path
from typing import Dict

from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults
from napkon_string_matching.types.dataset_definition import DatasetDefinitions
from napkon_string_matching.types.gecco_definition import GeccoDefinition
from napkon_string_matching.types.mapping import Mapping
from napkon_string_matching.types.questionnaire import Questionnaire
from napkon_string_matching.types.questionnaire_types.dataset_table import DatasetTable

CONFIG_GECCO_FILES = "gecco_definition"
CONFIG_GECCO83 = "gecco83"
CONFIG_GECCO_PLUS = "geccoplus"
CONFIG_GECCO_JSON = "json"
CONFIG_DATASET_DEFINITION = "dataset_definition"
CONFIG_FIELD_FILES = "files"
CONFIG_FIELD_MAPPINGS = "mappings"
CONFIG_FIELD_MATCHING = "matching"
CONFIG_VARIABLE_THRESHOLD = "variable_score_threshold"

RESULTS_FILE_PATTERN = "output/result_{score_threshold}_{compare_column}_{score_func}.xlsx"


logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, preparator: MatchPreparator, config: Dict, use_cache=True) -> None:
        self.preparator = preparator
        self.config = config
        self.gecco: GeccoDefinition = None
        self.questionnaires: Dict[str, Questionnaire] = None
        self.results: ComparisonResults = None
        self.mappings: Mapping = None
        self.use_cache = use_cache

        self._init_gecco_definition()
        self._init_dataset_definition()
        self._init_questionnaires()
        self._init_mappings()
        self.clear_results()

    def _init_gecco_definition(self) -> None:
        files: Dict[str, str] = self.config[CONFIG_GECCO_FILES]
        self.gecco = GeccoDefinition.prepare(
            file_name=files.get(CONFIG_GECCO_JSON),
            preparator=self.preparator,
            **self.config[CONFIG_FIELD_MATCHING],
            gecco83_file=files.get(CONFIG_GECCO83),
            geccoplus_file=files.get(CONFIG_GECCO_PLUS),
            use_cache=self.use_cache,
        )

        if self.gecco is None:
            logger.warning("didn't get any data")

    def _init_dataset_definition(self) -> None:
        file = self.config[CONFIG_DATASET_DEFINITION]
        self.dataset_def = DatasetDefinitions.read_json(file)

    def _init_questionnaires(self) -> None:
        self.questionnaires = {}
        for name, file in self.config[CONFIG_FIELD_FILES].items():
            dataset = DatasetTable.prepare(
                file_name=file,
                preparator=self.preparator,
                **self.config[CONFIG_FIELD_MATCHING],
                dataset_definitions=self.dataset_def[name],
                use_cache=self.use_cache,
            )

            if dataset is None:
                logger.warning("didn't get any data")
                continue
            else:
                self.questionnaires[name] = dataset

    def _init_mappings(self) -> None:
        self.mappings = Mapping()
        mapping_folder = Path(self.config[CONFIG_FIELD_MAPPINGS])
        for file in mapping_folder.glob("*.json"):
            mapping = Mapping.read_json(file)
            self.mappings.update(mapping)

    def clear_results(self) -> None:
        self.results = ComparisonResults()

    def match_gecco_with_questionnaires(self) -> None:
        for name, questionnaire in self.questionnaires.items():
            logger.info("compare gecco and %s", name)

            # Get existing mappings for first and second
            mappings = self.mappings[name]["gecco"].sources()

            matches = self.gecco.compare(
                questionnaire,
                left_existing_mappings=[],
                right_existing_mappings=mappings,
                left_name="gecco",
                right_name=name,
                **self.config[CONFIG_FIELD_MATCHING],
            )
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
                logger.info(
                    "compare %s %s and %s", prefix if prefix else "", name_first, name_second
                )

                # Get existing mappings for first and second
                mappings_first = self.mappings[name_first][name_second].sources()
                mappings_second = self.mappings[name_second][name_first].sources()

                matches = dataset_first.compare(
                    dataset_second,
                    mappings_first,
                    mappings_second,
                    left_name=name_first,
                    right_name=name_second,
                    **{**self.config[CONFIG_FIELD_MATCHING], **kwargs},
                )
                self.results[f"{prefix if prefix else ''}{name_first} vs {name_second}"] = matches

    def match_questionnaires_variables(self) -> ComparisonResults:
        self.match_questionnaires(
            prefix="var_",
            compare_column="Variable",
            score_threshold=self.config[CONFIG_FIELD_MATCHING][CONFIG_VARIABLE_THRESHOLD],
        )

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
            if comp.empty:
                continue

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
