import logging
from itertools import product
from pathlib import Path
from string import Template
from typing import Dict

from napkon_string_matching.constants import COHORTS
from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults
from napkon_string_matching.types.dataset_definition import DatasetDefinitions
from napkon_string_matching.types.dataset_table.dataset_table import DatasetTable
from napkon_string_matching.types.dataset_table.definitions import DatasetTablesDefinitions
from napkon_string_matching.types.dataset_table.definitions_types.excel_definitions import (
    DatasetTablesExcelDefinitions,
)
from napkon_string_matching.types.gecco_definition import GeccoDefinition
from napkon_string_matching.types.mapping import Mapping
from napkon_string_matching.types.questionnaire import Questionnaire
from napkon_string_matching.types.table_categories import TableCategories

CONFIG_GECCO_FILES = "gecco_definition"
CONFIG_GECCO83 = "gecco83"
CONFIG_GECCO_PLUS = "geccoplus"
CONFIG_GECCO_JSON = "json"
CONFIG_DATASET_DEFINITION = "dataset_definition"
CONFIG_FIELD_FILES = "files"
CONFIG_FIELD_MAPPINGS = "mappings"
CONFIG_FIELD_MATCHING = "matching"
CONFIG_VARIABLE_THRESHOLD = "variable_score_threshold"
CONFIG_TABLE_DEFINITIONS = "table_definitions"
CONFIG_TABLE_CATEGORIES = "categories_file"
CONFIG_TABLE_CATEGORIES_EXCEL = "categories_excel_file"
CONFIG_INPUT = "input"
CONFIG_INPUT_BASE_DIR = "base_dir"
CONFIG_OUTPUT_DIR = "output_dir"
CONFIG_CACHE_DIR = "cache_dir"

RESULTS_FILE_PATTERN = "result_{score_threshold}_{compare_column}_{score_func}.xlsx"


logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, preparator: MatchPreparator, config: Dict, use_cache=True) -> None:
        self.preparator = preparator
        self.config = config
        self.gecco: GeccoDefinition = None
        self.questionnaires: Dict[str, Questionnaire] = None
        self.results: ComparisonResults = None
        self.mappings: Mapping = None
        self.table_definitions: DatasetTablesDefinitions = None
        self.table_categories: TableCategories | None = None
        self.use_cache = use_cache
        self.dataset_def: DatasetDefinitions = None
        self.input_config: Dict | None = config.get(CONFIG_INPUT)
        self.input_dir = self.input_config.get(CONFIG_INPUT_BASE_DIR) if self.input_config else None
        self.cache_dir = config.get(CONFIG_CACHE_DIR)

        self._init_gecco_definition()
        self._init_table_categories()
        self._init_dataset_definition()
        self._init_dataset_table_definitions()
        self._init_questionnaires()
        self._init_mappings()
        self.clear_results()

    def _init_gecco_definition(self) -> None:
        files: Dict[str, str] = self.config[CONFIG_GECCO_FILES]
        file_name = self.__expand_path(files[CONFIG_GECCO_JSON])
        self.gecco = GeccoDefinition.prepare(
            file_name=file_name,
            preparator=self.preparator,
            **self.config[CONFIG_FIELD_MATCHING],
            gecco83_file=files.get(CONFIG_GECCO83),
            geccoplus_file=files.get(CONFIG_GECCO_PLUS),
            use_cache=self.use_cache,
            cache_dir=self.cache_dir,
        )

        if self.gecco is None:
            logger.warning("didn't get any data")

    def _init_dataset_definition(self) -> None:
        file = self.__expand_path(self.config[CONFIG_DATASET_DEFINITION])
        self.dataset_def = DatasetDefinitions.read_json(file)

    def _init_questionnaires(self) -> None:
        self.questionnaires = {}
        for name, file in self.config[CONFIG_FIELD_FILES].items():
            dataset = DatasetTable.prepare(
                file_name=self.__expand_path(file),
                preparator=self.preparator,
                **self.config[CONFIG_FIELD_MATCHING],
                dataset_definitions=self.dataset_def[name],
                table_categories=self.table_categories[name]
                if self.table_categories is not None
                else None,
                use_cache=self.use_cache,
                cache_dir=self.cache_dir,
            )

            if dataset is None:
                logger.warning("didn't get any data")
                continue
            else:
                self.questionnaires[name] = dataset

    def _init_dataset_table_definitions(self):
        file_name = self.__expand_path(self.config[CONFIG_TABLE_DEFINITIONS])
        definitions_file = Path(file_name)
        if definitions_file.exists():
            self.table_definitions = DatasetTablesExcelDefinitions.read_json(definitions_file)
        else:
            self.table_definitions = DatasetTablesExcelDefinitions()
            for cohort in COHORTS:
                if file := self.config[CONFIG_FIELD_FILES][cohort]:
                    self.table_definitions.add_from_file(
                        cohort,
                        self.__expand_path(file),
                        dataset_definitions=self.dataset_def[cohort],
                    )
            self.table_definitions.write_json(definitions_file)

    def _init_table_categories(self) -> None:
        file = self.config.get(CONFIG_TABLE_CATEGORIES)
        if file is not None:
            file = self.__expand_path(file)
            if Path(file).exists():
                self.table_categories = TableCategories.read_json(file)
            else:
                file_name = self.config.get(CONFIG_TABLE_CATEGORIES_EXCEL)
                if file_name:
                    excel_file = self.__expand_path(file_name)
                    if Path(excel_file).exists():
                        self.table_categories = TableCategories.read_excel(
                            excel_path=excel_file,
                            tables_definitions=self.table_definitions,
                        )
                        self.table_categories.write_json(file)

    def _init_mappings(self) -> None:
        self.mappings = Mapping()
        dir = self.__expand_path(self.config[CONFIG_FIELD_MAPPINGS])
        mapping_folder = Path(dir)
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
                cache_dir=self.cache_dir,
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
                    cache_dir=self.cache_dir,
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
        output_file = RESULTS_FILE_PATTERN.format(**format_args)
        if output_dir := self.config.get(CONFIG_OUTPUT_DIR):
            output_file = f"{output_dir}/{output_file}"

        self.results.write_excel(output_file)

    def __expand_path(self, path: str) -> str:
        return Template(path).substitute(input_base_dir=self.input_dir)
