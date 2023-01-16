import json
import logging
from typing import Dict, List
from uuid import uuid4

from napkon_string_matching.types.base.readable_json import ReadableJson
from napkon_string_matching.types.base.writable_json import WritableJson

logger = logging.getLogger(__name__)


class MappingEntry:
    def __init__(self, data: Dict[str, List[str]] | None = None) -> None:
        self._mappings: Dict[str, List[str]] = data if data is not None else {}

    def __getitem__(self, group_name: str) -> List[str]:
        return self._mappings[group_name]

    def __setitem__(self, group_name: str, value: List[str]) -> None:
        self._mappings[group_name] = value

    def has(
        self,
        group_name: str,
        identifier: str,
        second_group_name: str | None = None,
        second_identifier: str | None = None,
    ) -> bool:
        if second_group_name is not None and second_identifier is not None:
            return (
                identifier in group and second_identifier in group2
                if (group := self[group_name]) is not None and (group2 := self[second_group_name])
                else False
            )
        else:
            return identifier in group if (group := self[group_name]) is not None else False

    def add(self, group_name: str, identifier: str) -> None:
        if (group := self[group_name]) is None:
            self[group_name] = [identifier]
        else:
            if identifier not in group:
                group.append(identifier)

    def update(self, other) -> None:
        for group, identifiers in other.items():
            for identifier in identifiers:
                self.add(group, identifier)

    def dict(self) -> Dict[str, List[str]]:
        return self._mappings

    def num_entries_groups(self) -> Dict[str, int]:
        return {group: len(mappings) for group, mappings in self._mappings.items()}


class Mapping(ReadableJson, WritableJson):
    def __init__(self, data: Dict[str, Dict[str, List[str]]] | None = None) -> None:
        self._mappings: Dict[str, MappingEntry] = (
            {key: MappingEntry(data=entry) for key, entry in data.items()}
            if data is not None
            else {}
        )

    def get_group(self, id: str) -> MappingEntry | None:
        return self._mappings.get(id)

    def set_group(self, id: str, value: MappingEntry) -> None:
        self._mappings[id] = value

    def mapping_for_identifier(self, group: str, identifier: str) -> MappingEntry | None:
        for mapping in self._mappings.values():
            if mapping.has(group, identifier):
                return mapping
        return None

    def add_mapping(
        self, first_group: str, first_identifier: str, second_group: str, second_identifier: str
    ) -> MappingEntry:
        if (mapping := self.mapping_for_identifier(first_group, first_identifier)) is not None:
            mapping.add(second_group, second_identifier)
            return mapping
        else:
            id = uuid4().hex
            self.set_group(
                id,
                MappingEntry(
                    data={first_group: [first_identifier], second_group: [second_identifier]}
                ),
            )
            return self.get_group(id)

    def has_mapping(
        self,
        first_group_name: str,
        first_identifier: str,
        second_group_name: str,
        second_identifier: str,
    ) -> bool:
        for mappings in self._mappings.values():
            if mappings.has(
                first_group_name, first_identifier, second_group_name, second_identifier
            ):
                return True
        return False

    def filter_by_group(self, group_name: str) -> Dict[str, List[str]]:
        return {
            key: value[group_name] for key, value in self._mappings.items() if value[group_name]
        }

    def get_ids(self, group: str, identifier: str) -> List[str]:
        return [
            id
            for id, mappings in self._mappings.items()
            if (mapping := mappings[group]) and identifier in mapping
        ]

    def __iter__(self):
        return iter(self.items())

    def items(self):
        return self._mappings.items()

    def values(self):
        return self._mappings.values()

    def get_filtered(self, ids: List[str]):
        result = Mapping()
        result._mappings = {id: value for id, value in self if id in ids}
        return result

    def update(self, other) -> None:
        for id, mapping in other.items():
            if id in self._mappings:
                self.get_group(id).update(mapping)
            else:
                self.set_group(id, mapping)

    def update_values(self, other) -> None:
        for id, mapping in other.items():

            # Find out if any of the entries is already present
            existing_mapping = None
            for group, identifiers in mapping._mappings.items():
                for identifier in identifiers:
                    if map := self.mapping_for_identifier(group, identifier):
                        existing_mapping = map
                        break

            if existing_mapping:
                for group, identifiers in mapping._mappings.items():
                    for identifier in identifiers:
                        existing_mapping.add(group, identifier)
            else:
                self.update(Mapping(data={id: mapping.dict()}))

    def dict(self) -> Dict[str, Dict[str, List[str]]]:
        return {key: mapping.dict() for key, mapping in self._mappings.items()}

    def to_json(self, indent: int | None = None, *args, **kwargs):
        return json.dumps(self.dict(), indent=indent)

    def __len__(self) -> int:
        return len(self._mappings)

    def num_entries_groups(self) -> Dict[str, int]:
        result = {}
        for entry in self._mappings.values():
            n_entries = entry.num_entries_groups()
            for group, number in n_entries.items():
                if group in result:
                    result[group] += number
                else:
                    result[group] = number
        return result

    def num_entries_groups_str(self) -> str:
        result = [f"{group.upper()}: {count}" for group, count in self.num_entries_groups().items()]
        return ", ".join(result)

    @classmethod
    def read_json(cls, *args, **kwargs):
        result = super().read_json(*args, **kwargs)
        logger.info("read %i mappings (%s)", len(result), result.num_entries_groups_str())
        return result

    def write_json(self, *args, **kwargs) -> None:
        logger.info("write %i mappings (%s)", len(self), self.num_entries_groups_str())
        super().write_json(*args, **kwargs)
