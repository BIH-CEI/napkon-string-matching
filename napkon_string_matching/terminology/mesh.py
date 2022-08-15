import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
import psycopg2
from napkon_string_matching.compare.score_functions import fuzzy_match
from napkon_string_matching.terminology.provider_base import ProviderBase

CONFIG_FIELD_DB = "db"

TERMINOLOGY_COLUMN_TERM = "Term"
TERMINOLOGY_COLUMN_ID = "Id"
TERMINOLOGY_COLUMN_SCORE = "Score"

logger = logging.getLogger(__name__)


@dataclass(kw_only=True, slots=True)
class TableRequest:
    """
    Specifies how to address/extract data from the database
    """

    table_name: str
    """Name of the table to access"""

    id_column: str
    """Name of the column to use as an identifier"""

    term_column: str
    """Name of the column to use a the term"""


TERMINOLOGY_REQUEST_TERMS = [
    TableRequest(
        table_name="EntryTerms",
        id_column="MainHeadingsId",
        term_column="DescriptionGerman",
    ),
    TableRequest(
        table_name="MainHeadings",
        id_column="Id",
        term_column="DescriptionGerman",
    ),
]


TERMINOLOGY_REQUEST_HEADINGS = [
    TableRequest(
        table_name="MainHeadings",
        id_column="Id",
        term_column="DescriptionGerman",
    ),
]


class MeshConnector:
    """
    Generic connector to access MeSH from a database
    """

    def read_table(self, request: TableRequest) -> pd.DataFrame:
        """
        Read a single table from a database

        Attr
        ---
            request (TableRequest): Specifies how to address the data

        Returns
        ---
            DataFrame: Extracted data with columns for id and term
        """

        statement = (
            f'SELECT "{request.id_column}", "{request.term_column}" FROM "{request.table_name}";'
        )
        results = self._execute(statement)

        terms = pd.DataFrame(
            [{TERMINOLOGY_COLUMN_ID: id, TERMINOLOGY_COLUMN_TERM: term} for id, term in results]
        )

        # Drop rows that may not contain an ID or a term
        terms = terms.dropna(how="any")
        return terms

    def read_tables(self, requests: List[TableRequest]) -> pd.DataFrame:
        """
        Read mutiple tables from a database

        Attr
        ---
            requests (List[TableRequest]): List of requests that specify how to address the data

        Returns
        ---
            DataFrame: Extracted data with columns for id and term
        """
        terms_list = []
        for request in requests:
            part = self.read_table(request)
            terms_list.append(part)

        result = pd.concat(terms_list)

        # Reset the index to have sequential indices after combining multiple DataFrames
        result = result.reset_index(drop=True)
        return result

    @abstractmethod
    def _execute(self, statement: str):
        """
        Abstract function to allow database specific implementation
        """
        return


class PostgresMeshConnector(MeshConnector):
    """
    Postgres specific connector for MeSH database
    """

    def __init__(self, **kwargs) -> None:
        self._connect(**kwargs)

    def _del__(self):
        self._disconnect()

    def __enter__(self, **kwargs):
        self._connect(**kwargs)
        return self

    def __exit__(self, *args, **kwargs):
        self._disconnect()

    def _connect(self, **kwargs):
        connection_config = {
            "host": kwargs.pop("host", "localhost"),
            "port": kwargs.pop("port", 5432),
            "dbname": kwargs.pop("db", "mesh"),
            "user": kwargs.pop("user", "postgres"),
            "password": kwargs.pop("passwd", "meshterms"),
        }

        self.connection = psycopg2.connect(**connection_config)

    def _disconnect(self):
        # if connection is open
        if self.connection.closed == 0:
            self.connection.close()

    def _execute(self, statement: str) -> List[tuple]:
        cursor = None
        try:
            cursor = self.connection.cursor()

            cursor.execute(statement)
            result = cursor.fetchall()

            self.connection.commit()
            return result

        finally:
            cursor.close()


class MeshProvider(ProviderBase):
    def __init__(self, config) -> None:
        super().__init__()
        self.config = config

        self.term_requests = TERMINOLOGY_REQUEST_TERMS
        self.heading_requests = TERMINOLOGY_REQUEST_HEADINGS

    def initialize(self) -> None:
        if not self.initialized:
            logger.info("load terms from database...")
            with PostgresMeshConnector(**self.config[CONFIG_FIELD_DB]) as connector:
                logger.info("...load MeSH terms...")
                self._synonyms = connector.read_tables(self.term_requests)
                self._headings = connector.read_tables(self.heading_requests)
            logger.info(
                "...got %i headings and %i total synonyms",
                len(self._headings),
                len(self._synonyms),
            )

    def get_matches(
        self,
        term: List[str],
        score_threshold: float = 0.1,
    ) -> List[Tuple[str, str, float]]:
        """
        Generate tokens from term, references and headings

        Returns
        ---
            List[Tuple[str, str, float]]:   List of tuples
            (ID, Term, Score)
        """
        ref_copy = self.synonyms.copy(deep=True)

        term = " ".join(term)
        # Calculate the score for each combination
        ref_copy[TERMINOLOGY_COLUMN_SCORE] = np.vectorize(fuzzy_match)(
            ref_copy[TERMINOLOGY_COLUMN_TERM], term
        )

        # Get IDs above threshold
        ref_copy = (
            ref_copy[ref_copy[TERMINOLOGY_COLUMN_SCORE] >= score_threshold]
            .sort_values(by=TERMINOLOGY_COLUMN_SCORE, ascending=False)
            .drop_duplicates(subset=TERMINOLOGY_COLUMN_ID)
        )

        return list(ref_copy.itertuples(index=False, name=None))
