import unittest

from napkon_string_matching.terminology import (
    COLUMN_ID,
    COLUMN_TERM,
    REQUEST_TERMS,
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
            tables = connector.read_tables(REQUEST_TERMS)
            self.assertIsNotNone(tables)
            self.assertIn(COLUMN_TERM, tables)
            self.assertIn(COLUMN_ID, tables)
            self.assertTrue(tables.count()[COLUMN_ID] > 0)
