# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging

import napkon_string_matching
from napkon_string_matching.compare import score_functions
from napkon_string_matching.constants import (
    CONFIG_FIELD_DB,
    CONFIG_FIELD_FILES,
    CONFIG_FIELD_MATCHING,
    DATA_COLUMN_TOKEN_IDS,
    LOG_FORMAT,
)

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
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
        CONFIG_FIELD_FILES: [
            "input/hap_test.xlsx",
            "input/pop_test.xlsx",
            "input/suep_test.xlsx",
        ],
    }

    napkon_string_matching.match(config)
