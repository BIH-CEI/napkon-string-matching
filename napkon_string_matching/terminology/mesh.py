from abc import abstractmethod
from typing import List

import pandas as pd
import psycopg2

if __package__ == "":
    from table_request import TableRequest
else:
    from .table_request import TableRequest


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

        statement = f'SELECT "{request.id_column}", "{request.term_column}" FROM "{request.table_name}";'
        results = self._execute(statement)

        terms = pd.DataFrame([{"id": id, "term": term} for id, term in results])

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
        connection_config = {
            "host": kwargs.pop("host", "localhost"),
            "port": kwargs.pop("port", 5432),
            "dbname": kwargs.pop("db", "mesh"),
            "user": kwargs.pop("user", "postgres"),
            "password": kwargs.pop("passwd", "meshterms"),
        }

        self.connection = psycopg2.connect(**connection_config)

    def __del__(self):
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


if __name__ == "__main__":
    config = {
        "host": "localhost",
        "port": 5432,
        "db": "mesh",
        "user": "postgres",
        "passwd": "meshterms",
    }

    connector = PostgresMeshConnector(**config)

    requests = [
        TableRequest(
            table_name="EntryTerms",
            id_column="MainHeadingsId",
            term_column="DescriptionEnglish",
        ),
        TableRequest(
            table_name="EntryTerms",
            id_column="MainHeadingsId",
            term_column="DescriptionGerman",
        ),
        TableRequest(
            table_name="MainHeadings",
            id_column="Id",
            term_column="DescriptionEnglish",
        ),
        TableRequest(
            table_name="MainHeadings",
            id_column="Id",
            term_column="DescriptionGerman",
        ),
    ]
    tables = connector.read_tables(requests)
    pass
