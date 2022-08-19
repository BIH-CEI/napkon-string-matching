import unittest
from pathlib import Path

from napkon_string_matching.types.questionnaire import Questionnaire


class TestQuestionnaire(unittest.TestCase):
    def test_read_write(self):
        quest = Questionnaire(
            {
                "Identifier": ["1", "2", "3"],
                "words": ["one", "two", "three"],
                "arrays": [[1, "one"], [2, "two"], [3, "three"]],
            },
        )

        file = Path("test_" + __name__ + ".json")
        if file.exists():
            file.unlink()

        quest.write_json(file)
        result = Questionnaire.read_json(file)

        file.unlink()

        self.assertDictEqual(quest.to_dict(), result.to_dict())
