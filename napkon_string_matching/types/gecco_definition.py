import logging
from enum import Enum
from pathlib import Path

import pandas as pd

import napkon_string_matching.types.comparable as comp
from napkon_string_matching.types.base.writable_excel import WritableExcel
from napkon_string_matching.types.category import Category
from napkon_string_matching.types.comparable_data import (ComparableColumns,
                                                          ComparableData)


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


class GeccoDefinition(GeccoBase, ComparableData, WritableExcel):
    """
    Definitions for the GECCO dataset
    """
    __column_mapping__ = {}
    __category_type__ = GeccoCategory

    def map_for_comparable(self):
        result = super().map_for_comparable()
        result[comp.Columns.VARIABLE.value] = result[comp.Columns.IDENTIFIER.value]
        return result

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
            self.gen_term(category, parameter, choice)
            for category, parameter, choice in zip(self.category, self.parameter, self.choices)
        ]
        self.term = result
        logger.info("...done")

    @classmethod
    def read_original_format(cls, file_name: str | Path, *args, **kwargs):
        return cls.read_json(file_name, *args, **kwargs)

    def to_csv(self) -> str:
        return super(ComparableData, self.stringify_list_columns()).to_csv()

    def get_items(self):
        return [("Sheet1", self.stringify_list_columns())]

    def stringify_list_columns(self):
        gecco = GeccoDefinition(self.dataframe().copy(deep=True))
        gecco.choices = [
            " | ".join(choice) if isinstance(choice, list) else choice for choice in gecco.choices
        ]
        return gecco
