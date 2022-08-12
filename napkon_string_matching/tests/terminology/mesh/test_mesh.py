import unittest

from napkon_string_matching.terminology import (
    TERMINOLOGY_COLUMN_ID,
    TERMINOLOGY_COLUMN_TERM,
    TERMINOLOGY_REQUEST_TERMS,
    PostgresMeshConnector,
)
from napkon_string_matching.tests import DISABLE_DB_TESTS


class TestPostgresMeshConnector(unittest.TestCase):
    def setUp(self):
        self.config = {
            "host": "localhost",
            "port": 5432,
            "db": "mesh",
            "user": "postgres",
            "passwd": "meshterms",
        }

    @unittest.skipIf(DISABLE_DB_TESTS, "db container may not be available")
    def test_read_tables(self):
        with PostgresMeshConnector(**self.config) as connector:
            tables = connector.read_tables(TERMINOLOGY_REQUEST_TERMS)
            self.assertIsNotNone(tables)
            self.assertIn(TERMINOLOGY_COLUMN_TERM, tables)
            self.assertIn(TERMINOLOGY_COLUMN_ID, tables)
            self.assertTrue(tables.count()[TERMINOLOGY_COLUMN_ID] > 0)
