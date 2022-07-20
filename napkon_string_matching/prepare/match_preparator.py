from typing import List

from napkon_string_matching.terminology import (
    REQUEST_HEADINGS,
    REQUEST_TERMS,
    PostgresMeshConnector,
    TableRequest,
)


class MatchPreparator:
    def __init__(self, dbConfig: dict):
        self.dbConfig = dbConfig

    def load_terms(
        self,
        term_requests: List[TableRequest] = REQUEST_TERMS,
        heading_requests: List[TableRequest] = REQUEST_HEADINGS,
    ):
        with PostgresMeshConnector(**self.dbConfig) as connector:
            self.terms = connector.read_tables(term_requests)
            self.headings = connector.read_tables(heading_requests)
