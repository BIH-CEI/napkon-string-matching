import unittest
from pathlib import Path

from napkon_string_matching.types.gecco_definition import GeccoDefinition


class TestGeccoDefinition(unittest.TestCase):
    def test_write_read(self):
        definition = {
            "Id": ["gecc_1", "gecc_2-1", "gecc_83+1"],
            "Category": ["A", "B", "C"],
            "Parameter": ["Wörter", "dass", "mit&"],
            "Choices": [["a", "b", "c"], "foo", None],
        }

        gecco = GeccoDefinition(definition)

        test_file = Path("test_ " + __name__ + ".json")
        if test_file.exists():
            test_file.unlink()

        gecco.write_json(test_file)
        result = GeccoDefinition.from_json(test_file)

        test_file.unlink()

        self.assertDictEqual(gecco.to_dict(), result.to_dict())
