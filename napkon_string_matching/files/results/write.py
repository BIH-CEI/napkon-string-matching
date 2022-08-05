import logging
from pathlib import Path
from unicodedata import category
from xml.dom.minidom import Identified

import pandas as pd

logger = logging.getLogger(__name__)

from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_MATCHES,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_VARIABLE,
)
from napkon_string_matching.files.results.constants import (
    RESULT_COLUMN_IDENTIFIER,
    RESULT_COLUMN_MATCH_IDENTIFIER,
    RESULT_COLUMN_MATCH_SCORE,
    RESULT_COLUMN_MATCH_TERM,
    RESULT_COLUMN_TERM,
    RESULT_COLUMN_VARIABLE,
)


def write(file_name: str | Path, results: pd.DataFrame) -> None:
    file = Path(file_name)
    if not file.parent.exists():
        file.parent.mkdir(parents=True)

    logger.info("prepare result data for output...")
    results_list = []
    for index, row in results.iterrows():
        categories = row[DATA_COLUMN_CATEGORIES]
        question = row[DATA_COLUMN_QUESTION]
        item = row[DATA_COLUMN_ITEM]

        term = (
            (",".join(categories) + ":") if categories else ""
        ) + f"{question}:{item}"

        base_dict = {
            RESULT_COLUMN_IDENTIFIER: index,
            RESULT_COLUMN_TERM: term,
            RESULT_COLUMN_VARIABLE: row[DATA_COLUMN_VARIABLE],
        }

        matches = row[DATA_COLUMN_MATCHES]
        if not matches:
            results_list.append(base_dict)
            continue

        for score, identifier, term in matches:
            extended_dict = {
                **base_dict,
                RESULT_COLUMN_MATCH_SCORE: score,
                RESULT_COLUMN_MATCH_IDENTIFIER: identifier,
                RESULT_COLUMN_MATCH_TERM: term,
            }

            results_list.append(extended_dict)

    results_df = pd.DataFrame(results_list)

    logger.info("write result to %s", str(file))
    file.write_text(results_df.to_csv(index=False), encoding="utf-8")
