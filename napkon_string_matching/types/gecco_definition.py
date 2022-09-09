import logging
from enum import Enum

import napkon_string_matching.types.comparable as comp
import pandas as pd
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import ComparableColumns, ComparableData


class Columns(Enum):
    CATEGORY = "Category"
    PARAMETER = "Parameter"
    CHOICES = "Choices"


logger = logging.getLogger(__name__)


class GeccoBase:
    __columns__ = list(ComparableColumns) + list(Columns)
    __category_column__ = Columns.CATEGORY.value


class GeccoCategory(GeccoBase, Category):
    pass


class GeccoDefinition(GeccoBase, ComparableData):
    __column_mapping__ = {ComparableColumns.IDENTIFIER.value: comp.Columns.VARIABLE.value}
    __category_type__ = GeccoCategory

    def concat(self, other):
        if not isinstance(other, GeccoDefinition):
            raise TypeError(
                "'other' should be of type '{}' but is of type '{}'".format(
                    type(self).__name__, type(other).__name__
                )
            )

        return GeccoDefinition(pd.concat([self._data, other._data], ignore_index=True))

    def add_terms(self, language: str = "german"):
        logger.info("add terms...")
        result = [
            ComparableData.gen_term([category, parameter], language=language)
            for category, parameter in zip(self.category, self.parameter)
        ]
        self.term = result
        logger.info("...done")

    def filter(self, filter_column: str, filter_prefix: str):
        pass
