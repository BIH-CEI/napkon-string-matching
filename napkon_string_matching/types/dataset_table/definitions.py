import json
from typing import Dict, List

from napkon_string_matching.constants import COHORTS
from napkon_string_matching.types.base.readable_json import ReadableJson
from napkon_string_matching.types.base.writable_json import WritableJson

JSON_SUBGROUP_NAMES = "subgroup_names"
JSON_GROUPS = "groups"
JSON_SUBGROUPS = "subgroups"


class DatasetTableDefinitions:
    def __init__(
        self,
        data: Dict | None = None,
        subgroup_names: Dict[str, str] | None = None,
        groups: Dict[str, str] | None = None,
        subgroups: Dict[str, List[str]] | None = None,
    ):
        if (
            data is not None
            and JSON_SUBGROUP_NAMES in data
            and JSON_GROUPS in data
            and JSON_SUBGROUPS in data
        ):
            self.subgroup_names = data[JSON_SUBGROUP_NAMES]
            self.groups = data[JSON_GROUPS]
            self.subgroups = data[JSON_SUBGROUPS]
        else:
            self.subgroup_names = subgroup_names if subgroup_names is not None else {}
            self.groups = groups if groups is not None else {}
            self.subgroups = subgroups if subgroups is not None else {}

    def concat(self, others: List):
        result = self.__class__(
            subgroup_names=self.subgroup_names, groups=self.groups, subgroups=self.subgroups
        )
        result.subgroup_names.update({k: v for d in others for k, v in d.subgroup_names.items()})
        result.groups.update({k: v for d in others for k, v in d.groups.items()})
        result.subgroups.update({k: v for d in others for k, v in d.subgroups.items()})
        return result

    def to_dict(self):
        data = {
            JSON_SUBGROUP_NAMES: self.subgroup_names,
            JSON_GROUPS: self.groups,
            JSON_SUBGROUPS: self.subgroups,
        }
        return data

    def to_json(self, *args, **kwargs) -> str:
        return json.dumps(self.to_dict(), *args, **kwargs)

    def __len__(self) -> int:
        return len(self.subgroup_names) + len(self.groups) + len(self.subgroups)


class DatasetTablesDefinitions(ReadableJson, WritableJson):
    def __init__(self, data: Dict | None = None):
        self.data: Dict[str, DatasetTableDefinitions] = {}
        if data:
            for cohort in COHORTS:
                if definition := data.get(cohort):
                    self[cohort] = DatasetTableDefinitions(definition)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, item, value):
        self.data[item] = value

    def to_dict(self):
        data = {key: value.to_dict() for key, value in self.data.items()}
        return data

    def to_json(self, orient=None, *args, **kwargs) -> str:
        return json.dumps(self.to_dict(), *args, **kwargs)

    def __len__(self) -> int:
        return sum([len(value) for value in self.data.values()])
