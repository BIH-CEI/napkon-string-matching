from datetime import timedelta

import numpy as np
import pandas as pd
from rapidfuzz import fuzz


def gen_token(
    term: str, reference: pd.DataFrame, headings: pd.DataFrame, score_threshold: int
):
    ref_copy = reference.copy(deep=True)

    ref_copy["score"] = np.vectorize(fuzz.WRatio)(ref_copy["term"], term)

    # Get IDs above threshold
    ref_copy = ref_copy[ref_copy["score"] >= score_threshold].drop_duplicates(
        subset="id"
    )

    # Get the corsponding headings
    ref_copy = ref_copy.merge(headings, on="id", suffixes=(None, "_heading"))

    result = {
        "terms": list(ref_copy["term_heading"].values),
        "ids": list(ref_copy["id"].values),
        "mesh": list(ref_copy.values),
    }

    return result


if __name__ == "__main__":

    from time import perf_counter

    from terminology.constants import REQUEST_HEADINGS, REQUEST_TERMS
    from terminology.mesh import PostgresMeshConnector
    from terminology.table_request import TableRequest

    config = {
        "host": "localhost",
        "port": 5432,
        "db": "mesh",
        "user": "postgres",
        "passwd": "meshterms",
    }

    connector = PostgresMeshConnector(**config)

    references = connector.read_tables(REQUEST_TERMS)
    headings = connector.read_tables(REQUEST_HEADINGS)

    term = "Dialyse nach Entlassung"
    start = perf_counter()
    result = gen_token(term, references, headings, score_threshold=90)
    end = perf_counter()
    print(timedelta(seconds=end - start))
    pass
