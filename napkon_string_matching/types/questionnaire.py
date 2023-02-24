import logging
from enum import Enum
from typing import List

import pandas as pd

import napkon_string_matching.types.comparable as comp
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    SHEET = "Sheet"
    FILE = "File"
    HEADER = "Header"
    QUESTION = "Question"
    OPTIONS = "Options"
    VARIABLE = "Variable"
    PARAMETER = "Parameter"
    UID = "Uid"
    CATEGORY = "Category"


logger = logging.getLogger(__name__)


class QuestionnaireBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.CATEGORY.value


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

        return self.__class__(
            data=pd.concat([self._data, *[other._data for other in others]], ignore_index=True)
        )

    def add_terms(self):
        logger.info("add terms...")
        result = [
            self.gen_term(*header, question, parameter)
            if header
            else self.gen_term(question, parameter)
            for header, question, parameter in zip(self.header, self.question, self.parameter)
        ]
        self.term = result
        logger.info("...done")
