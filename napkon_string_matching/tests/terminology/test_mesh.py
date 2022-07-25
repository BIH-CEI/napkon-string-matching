import unittest

from napkon_string_matching.terminology import (
    TERMINOLOGY_COLUMN_ID,
    TERMINOLOGY_COLUMN_TERM,
    TERMINOLOG_REQUEST_TERMS,
    PostgresMeshConnector,
)


class TestPostgresMeshConnector(unittest.TestCase):
    def setUp(self):
        self.config = {
            "host": "localhost",
            "port": 5432,
            "db": "mesh",
            "user": "postgres",
            "passwd": "meshterms",
        }

    @unittest.skip("db container may not be available")
    def test_read_tables(self):
        with PostgresMeshConnector(**self.config) as connector:
            tables = connector.read_tables(TERMINOLOG_REQUEST_TERMS)
            self.assertIsNotNone(tables)
            self.assertIn(TERMINOLOGY_COLUMN_TERM, tables)
            self.assertIn(TERMINOLOGY_COLUMN_ID, tables)
            self.assertTrue(tables.count()[TERMINOLOGY_COLUMN_ID] > 0)
