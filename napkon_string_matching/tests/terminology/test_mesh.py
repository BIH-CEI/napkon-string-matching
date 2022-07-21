import unittest

from napkon_string_matching.terminology import REQUEST_TERMS, PostgresMeshConnector


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
            self.assertIn("term", tables)
            self.assertIn("id", tables)
            self.assertTrue(tables.count()["id"] > 0)
