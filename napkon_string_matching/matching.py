# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from itertools import product
from pathlib import Path
from typing import Dict, List

import pandas as pd

from napkon_string_matching.compare import compare, enhance_datasets_with_matches
from napkon_string_matching.constants import (
    CONFIG_FIELD_DB,
    CONFIG_FIELD_FILES,
    CONFIG_FIELD_MATCHING,
    DATA_COLUMN_MATCHES,
    LOG_FORMAT,
    RESULTS_FILE_PATTERN,
)
from napkon_string_matching.files import dataframe, dataset_table, results
from napkon_string_matching.prepare import MatchPreparator

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def match(config: Dict) -> None:
    preparator = get_preparator(config[CONFIG_FIELD_DB])

    datasets = {}
    for file in config[CONFIG_FIELD_FILES]:
        name = Path(file).stem
        dataset = prepare(file, preparator, **config[CONFIG_FIELD_MATCHING])
        datasets[name] = dataset

    comparisons = {}
    for entry_left, entry_right in product(datasets.items(), datasets.items()):
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
        if key not in comparisons:
            logger.info("compare %s and %s", name_first, name_second)
            matches = compare(
                dataset_first, dataset_second, **config[CONFIG_FIELD_MATCHING]
            )
            comparisons[key] = matches

    for key, matches in comparisons.items():
        name_left, name_right = key

        dataset_left = datasets[name_left]
        dataset_right = datasets[name_right]

        enhance_datasets_with_matches(dataset_left, dataset_right, matches)

        datasets[name_left] = dataset_left
        datasets[name_right] = dataset_right

    analysis = _analyse(datasets)
    _print_analysis(analysis)

    for name, dataset in datasets.items():
        format_args = {
            **config[CONFIG_FIELD_MATCHING],
            "file_name": name,
            "score_func": config[CONFIG_FIELD_MATCHING]["score_func"].replace("_", "-"),
        }
        results.write(RESULTS_FILE_PATTERN.format(**format_args), dataset)


def get_preparator(dbConfig):

    return MatchPreparator(dbConfig)


def prepare(
    file_name: str,
    preparator: MatchPreparator,
    calculate_tokens: bool = False,
    *args,
    **kwargs,
) -> pd.DataFrame:
    file = Path(file_name)
    logger.info(f"prepare file {file.name}")

    output_dir = Path("prepared")
    FILE_PATTERN = file.stem + "_{}.json"

    # File names for all cache files
    # Order here is unprocessed -> terms -> prepared
    unprocessed_file = output_dir / FILE_PATTERN.format("unprocessed")
    terms_file = output_dir / FILE_PATTERN.format("terms")
    prepared_file = output_dir / FILE_PATTERN.format("prepared")

    # Create output director if not existing
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    # If prepared already exists, read it and return data
    if prepared_file.exists():
        logger.info("using previously cached prepared file")
        data = dataframe.read(prepared_file)
        return data

    # If term file exists read its data
    if terms_file.exists():
        logger.info("using previously cached terms file")
        data = dataframe.read(terms_file)
    else:
        # If unprocessed file exists, read it; otherwise calculate
        if unprocessed_file.exists():
            logger.info("using previously cached unprocessed file")
            data = dataframe.read(unprocessed_file)
        else:
            data = dataset_table.read(file)
            dataframe.write(unprocessed_file, data)

        # No matter if unprocessed data was read from cache or dataset file,
        # the terms still needs to be generated
        preparator.add_terms(data)
        dataframe.write(terms_file, data)

    # No matter if terms data was read or calculated,
    # the tokens still need to be generated if required
    if calculate_tokens:
        preparator.add_tokens(data, score_threshold=90, timeout=30)
        dataframe.write(prepared_file, data)

    return data


def _analyse(dfs: List[pd.DataFrame]) -> Dict[str, Dict[str, str]]:
    result = {}
    for name, df in dfs.items():
        df_result = {
            "matched": "{}/{}".format(len(df[df[DATA_COLUMN_MATCHES].notna()]), len(df))
        }
        result[name] = df_result
    return result


def _print_analysis(analysis: Dict[str, Dict[str, str]]) -> None:
    for name, item in analysis.items():
        entries = []
        for key, value in item.items():
            entries.append("{}: {}".format(key, value))
        logger.info("%s\t%s", name, "\t".join(entries))
