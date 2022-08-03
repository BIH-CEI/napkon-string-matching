# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from itertools import product
from pathlib import Path

import pandas as pd

from napkon_string_matching.compare import compare, score_functions
from napkon_string_matching.constants import (
    CONFIG_FIELD_DB,
    CONFIG_FIELD_MATCHING,
    DATA_COLUMN_TOKEN_IDS,
    LOG_FORMAT,
    RESULTS_FILE_PATTERN,
)
from napkon_string_matching.files import dataframe, dataset_table, results
from napkon_string_matching.prepare import MatchPreparator

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_preparator(dbConfig):

    preparator = MatchPreparator(dbConfig)
    preparator.load_terms()

    return preparator


def prepare(file_name: str, preparator: MatchPreparator) -> pd.DataFrame:
    file = Path(file_name)
    logger.info(f"prepare file {file.name}")

    prepared_file = Path("prepared") / (file.stem + "_prepared.json")

    if not prepared_file.parent.exists():
        prepared_file.parent.mkdir(parents=True)

    if prepared_file.exists():
        logger.info("using previously prepared file")
        data = dataframe.read(prepared_file)
        return data

    data = dataset_table.read(file)
    preparator.add_terms(data)
    preparator.add_tokens(data, score_threshold=90, timeout=30)

    logger.info("writing prepared data")
    dataframe.write(prepared_file, data)

    return data


def main():

    config = {
        CONFIG_FIELD_DB: {
            "host": "localhost",
            "port": 5432,
            "db": "mesh",
            "user": "postgres",
            "passwd": "meshterms",
        },
        CONFIG_FIELD_MATCHING: {
            "score_threshold": 0.9,
            "compare_column": DATA_COLUMN_TOKEN_IDS,
            "score_func": score_functions.intersection_vs_union,
        },
    }

    preparator = get_preparator(config[CONFIG_FIELD_DB])

    files = ["input/hap_test.xlsx", "input/pop_test.xlsx", "input/suep_test.xlsx"]

    datasets = []
    for file in files:
        name = Path(file).stem
        dataset = prepare(file, preparator)
        datasets.append((name, dataset))

    comparisons = set()
    for entry_left, entry_right in product(datasets, datasets):
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
            compare(dataset_first, dataset_second, **config[CONFIG_FIELD_MATCHING])
            comparisons.add(key)

    for name, dataset in datasets:
        format_args = {
            **config[CONFIG_FIELD_MATCHING],
            "file_name": name,
            "score_func": config[CONFIG_FIELD_MATCHING]["score_func"].__name__.replace(
                "_", "-"
            ),
        }
        results.write(RESULTS_FILE_PATTERN.format(**format_args), dataset)


if __name__ == "__main__":
    main()
