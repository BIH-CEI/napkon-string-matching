from typing import Dict, List

import napkon_string_matching.types.comparable_data as cd
from napkon_string_matching.types.kds_definition import Columns, KdsDefinition


class FhirKdsDefinition(KdsDefinition):
    @classmethod
    def read_original_format(cls, elements: List[Dict[str, Dict[str, str]]], *args, **kwargs):
        result = [
            {
                cd.Columns.IDENTIFIER.value: element["id"],
                Columns.PARAMETER.value: element.get("description")
                if element.get("description")
                else element.get("short"),
                Columns.CATEGORY.value: None,
            }
            for element in elements
        ]
        return cls(data=result)
