# The script calculates the similarity ratio using the Levenshtein
# distance between the item names from SUEP, HAP and POP.

import logging
from pathlib import Path

import pandas as pd

from napkon_string_matching.files import dataframe, dataset_table
from napkon_string_matching.prepare import MatchPreparator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_preparator():
    dbConfig = {
        "host": "localhost",
        "port": 5432,
        "db": "mesh",
        "user": "postgres",
        "passwd": "meshterms",
    }

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
        logger.info(f"using previously prepared file")
        data = dataframe.read(prepared_file)
        return data

    data = dataset_table.read(file)
    preparator.add_terms(data)
    preparator.add_tokens(data, score_threshold=90)

    logger.info(f"writing prepared data")
    dataframe.write(prepared_file, data)

    return data


def main():
    preparator = get_preparator()

    hap = prepare("input/hap_test.xlsx", preparator)
    pop = prepare("input/pop_test.xlsx", preparator)
    suep = prepare("input/suep_test.xlsx", preparator)


if __name__ == "__main__":
    main()
