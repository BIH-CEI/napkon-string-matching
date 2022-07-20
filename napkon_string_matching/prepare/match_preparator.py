from typing import List

import numpy as np
import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_TERM,
)
from napkon_string_matching.prepare.generate import gen_term
from napkon_string_matching.terminology import (
    REQUEST_HEADINGS,
    REQUEST_TERMS,
    PostgresMeshConnector,
    TableRequest,
)


class MatchPreparator:
    def __init__(self, dbConfig: dict):
        self.dbConfig = dbConfig
        self.terms = None
        self.headings = None

    def load_terms(
        self,
        term_requests: List[TableRequest] = REQUEST_TERMS,
        heading_requests: List[TableRequest] = REQUEST_HEADINGS,
    ):
        with PostgresMeshConnector(**self.dbConfig) as connector:
            self.terms = connector.read_tables(term_requests)
            self.headings = connector.read_tables(heading_requests)

    def add_terms(self, df: pd.DataFrame):
        if self.terms is None or self.headings is None:
            raise RuntimeError("'terms' and/or 'headings' not initialized")

        df[DATA_COLUMN_TERM] = np.vectorize(gen_term)(
            df[DATA_COLUMN_CATEGORIES], df[DATA_COLUMN_QUESTION], df[DATA_COLUMN_ITEM]
        )
