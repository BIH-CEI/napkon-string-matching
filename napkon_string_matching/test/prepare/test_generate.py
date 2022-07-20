import json
import unittest
from pathlib import Path

import pandas as pd
from napkon_string_matching.prepare import gen_token


class TestGenToken(unittest.TestCase):
    def setUp(self):
        data_dir = Path("napkon_string_matching/test/prepare/data")

        self.references = pd.DataFrame(
            json.loads((data_dir / "references.json").read_text())
        )
        self.headings = pd.DataFrame(
            json.loads((data_dir / "headings.json").read_text())
        )

    def test_gen_token(self):
        term = "Dialyse nach Entlassung"
        result = gen_token(term, self.references, self.headings, score_threshold=90)
        self.assertIsNotNone(result)
        self.assertIn("terms", result)
        self.assertEqual(len(result["terms"]), 1)
        self.assertIn("Dialyse", result["terms"])


if __name__ == "__main__":
    unittest.main()
