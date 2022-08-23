# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from itertools import product
from pathlib import Path
from typing import Dict

from napkon_string_matching.prepare.match_preparator import MatchPreparator
from napkon_string_matching.types.comparable import ComparisonResults
from napkon_string_matching.types.questionnaire import Questionnaire

RESULTS_FILE_PATTERN = "output/{file_name}_{score_threshold}_{compare_column}_{score_func}.csv"

CONFIG_FIELD_PREPARE = "prepare"
CONFIG_FIELD_MATCHING = "matching"
CONFIG_FIELD_FILES = "files"


logger = logging.getLogger(__name__)


def match(config: Dict) -> None:
    preparator = get_preparator(config[CONFIG_FIELD_PREPARE])

    datasets = {}
    for file in config[CONFIG_FIELD_FILES]:
        name = Path(file).stem
        dataset = prepare(file, preparator, **config[CONFIG_FIELD_MATCHING])

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

    for name, dataset in datasets.items():
        format_args = {
            **config[CONFIG_FIELD_MATCHING],
            "file_name": name,
            "score_func": config[CONFIG_FIELD_MATCHING]["score_func"].replace("_", "-"),
        }
        results.write(RESULTS_FILE_PATTERN.format(**format_args), dataset)


def get_preparator(config):
    return MatchPreparator(config)


def prepare(
    file_name: str,
    preparator: MatchPreparator,
    calculate_tokens: bool = False,
    *args,
    **kwargs,
) -> Questionnaire:
    """
    Reads a questionnaire from file. If `calculate_tokens == True` tokens are also generated
    using the provided preparator.
    """
    file = Path(file_name)
    logger.info(f"prepare file {file.name}")

    output_dir = Path("prepared")

    # Build output file pattern
    file_pattern = [file.stem]

    if "filter_column" in kwargs:
        file_pattern.append(kwargs["filter_column"])

    if "filter_prefix" in kwargs:
        file_pattern.append(kwargs["filter_prefix"])

    file_pattern.append("{}.json")

    file_pattern = "_".join(file_pattern)

    # File names for all cache files
    # Order here is unprocessed -> terms -> prepared
    unprocessed_file = output_dir / file_pattern.format("unprocessed")
    terms_file = output_dir / file_pattern.format("terms")
    prepared_file = output_dir / file_pattern.format("prepared")

    # Create output director if not existing
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # If prepared already exists, read it and return data
    if prepared_file.exists():
        logger.info("using previously cached prepared file")
        data = Questionnaire.read_json(prepared_file)
        return data

    # If term file exists read its data
    if terms_file.exists():
        logger.info("using previously cached terms file")
        data = Questionnaire.read_json(terms_file)
    else:
        # If unprocessed file exists, read it; otherwise calculate
        if unprocessed_file.exists():
            logger.info("using previously cached unprocessed file")
            data = Questionnaire.read_json(unprocessed_file)
        else:
            data = Questionnaire.read_dataset_table(file, *args, **kwargs)

            if data is None:
                return None

            data.write_json(unprocessed_file)

        # No matter if unprocessed data was read from cache or dataset file,
        # the terms still needs to be generated
        preparator.add_terms(data)
        data.write_json(terms_file)

    # No matter if terms data was read or calculated,
    # the tokens still need to be generated if required
    if calculate_tokens:
        preparator.add_tokens(data, score_threshold=90, timeout=30)
        data.write_json(prepared_file)

    return data


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
