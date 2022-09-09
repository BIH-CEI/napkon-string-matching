import logging
from enum import Enum
from typing import List

import napkon_string_matching.types.comparable as comp
import pandas as pd
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    ITEM = "Item"
    SHEET = "Sheet"
    FILE = "File"
    HEADER = "Header"
    QUESTION = "Question"
    OPTIONS = "Options"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    UID = "Uid"


logger = logging.getLogger(__name__)


class QuestionnaireBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.SHEET.value


class QuestionnaireCategory(QuestionnaireBase, Category):
    pass


class Questionnaire(QuestionnaireBase, ComparableData):
    __column_mapping__ = {Columns.PARAMETER.value: comp.Columns.PARAMETER.value}
    __category_type__ = QuestionnaireCategory

    def concat(self, others: List):
        if len(others) == 0:
            return self

        if not isinstance(others[0], Questionnaire):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(others[0]).__name__
                )
            )

        return Questionnaire(
            pd.concat([self._data, *[other._data for other in others]], ignore_index=True)
        )

    def add_terms(self, language: str = "german"):
        logger.info("add terms...")
        result = [
            Questionnaire.gen_term(header, question, item, language=language)
            for header, question, item in zip(self.header, self.question, self.item)
        ]
        self.term = result
        logger.info("...done")

    @staticmethod
    def gen_term(categories: List[str], question: str, item: str, language: str = "german") -> str:
        term_parts = get_term_parts(categories, question, item)
        return ComparableData.gen_term(term_parts, language)


def get_term_parts(categories: List[str], question: str, item: str) -> List[str]:
    term_parts = []

    if categories:
        term_parts += categories
    if question:
        term_parts.append(question)
    if item:
        term_parts.append(item)

    return term_parts
