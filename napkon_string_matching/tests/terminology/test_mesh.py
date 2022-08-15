import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.terminology.mesh import (
    TERMINOLOGY_COLUMN_ID,
    TERMINOLOGY_COLUMN_TERM,
    TERMINOLOGY_REQUEST_TERMS,
    MeshProvider,
    PostgresMeshConnector,
)
from napkon_string_matching.tests import DISABLE_DB_TESTS


class TestMeshProvider(unittest.TestCase):
    def test_get_matches(self):
        data_dir = Path("napkon_string_matching/tests/data")
        references = pd.DataFrame(json.loads((data_dir / "references.json").read_text()))
        headings = pd.DataFrame(json.loads((data_dir / "headings.json").read_text()))

        provider = MeshProvider(None)
        provider._headings = headings
        provider._synonyms = references

        term = "Dialyse nach Entlassung"
        results = provider.get_matches(term)
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)

        id, token, score = results[0]
        self.assertIn("Dialyse", token)
        self.assertGreater(score, 0)


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
