import json
import logging
from typing import Dict, List, Tuple
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

    def get(self, group_name: str, default=None):
        return self._mappings.get(group_name, default)

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
                if (group := self.get(group_name)) is not None
                and (group2 := self.get(second_group_name))
                else False
            )
        else:
            return identifier in group if (group := self.get(group_name)) is not None else False

    def add(self, group_name: str, identifier: str) -> None:
        try:
            group = self[group_name]
            group.append(identifier)
        except:
            self[group_name] = [identifier]

    def update(self, other) -> None:
        for group, identifiers in other.dict().items():
            for identifier in identifiers:
                self.add(group, identifier)

    def dict(self) -> Dict[str, List[str]]:
        return self._mappings

    def num_entries_groups(self) -> Dict[str, int]:
        return {group: len(mappings) for group, mappings in self._mappings.items()}

    def get_group_names(self) -> List[str]:
        return list(self._mappings.keys())

    def get_group_combination(
        self, group_left: str, group_right: str
    ) -> Tuple[List[str], List[str]] | None:
        try:
            return self[group_left], self[group_right]
        except KeyError:
            return None


class Mapping(ReadableJson, WritableJson):
    def __init__(self, data: Dict[str, Dict[str, List[str]]] | None = None) -> None:
        self._mappings: Dict[str, MappingEntry] = (
            {key: MappingEntry(data=entry) for key, entry in data.items()}
            if data is not None
            else {}
        )

    def get_group_names(self) -> List[str]:
        result = set()
        for id_group in self._mappings.values():
            group_names = id_group.get_group_names()
            result.update(group_names)
        return list(result)

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
        self,
        first_group: str,
        first_identifier: str,
        second_group: str,
        second_identifier: str,
        id_reference=None,
    ) -> MappingEntry:
        if (
            mapping := self.get_mapping(
                first_group, first_identifier, second_group, second_identifier
            )
        ) is None:
            id = uuid4().hex

            if id_reference:
                if id_tmp := id_reference.get_first_id(first_group, first_identifier):
                    id = id_tmp
                elif id_tmp := id_reference.get_first_id(second_group, second_identifier):
                    id = id_tmp

            self.set_group(
                id,
                MappingEntry(
                    data={first_group: [first_identifier], second_group: [second_identifier]}
                ),
            )
            return self.get_group(id)
        else:
            return mapping

    def update_mapping(
        self,
        first_group: str,
        first_identifier: str,
        second_group: str,
        second_identifier: str,
        id_reference=None,
    ) -> MappingEntry:
        if (mapping := self.mapping_for_identifier(first_group, first_identifier)) is not None:
            mapping.add(second_group, second_identifier)
            return mapping
        elif (mapping := self.mapping_for_identifier(second_group, second_identifier)) is not None:
            mapping.add(first_group, first_identifier)
            return mapping
        else:
            return self.add_mapping(
                first_group,
                first_identifier,
                second_group,
                second_identifier,
                id_reference=id_reference,
            )

    def get_mapping(
        self,
        first_group_name: str,
        first_identifier: str,
        second_group_name: str,
        second_identifier: str,
    ) -> MappingEntry | None:
        for mappings in self._mappings.values():
            if mappings.has(
                first_group_name, first_identifier, second_group_name, second_identifier
            ):
                return mappings
        return None

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

    def get_first_id(self, group: str, identifier: str) -> str | None:
        for id, mappings in self._mappings.items():
            if (mapping := mappings.get(group)) and identifier in mapping:
                return id
        return None

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

    def add_values(self, other) -> None:
        for id, mapping in other.items():
            self._recursive_add(list(mapping._mappings.items()))

    def _recursive_add(self, mappings: List[Tuple[str, List[str]]]):
        if len(mappings) > 2:
            mapping = mappings.pop()
            values_right = self._recursive_add(mappings)

            group_left, mappings_left = mapping
            values_left = [(group_left, entry) for entry in mappings_left]
        else:
            group_left, mappings_left = mappings[0]
            group_right, mappings_right = mappings[1]

            values_left = [(group_left, entry) for entry in mappings_left]
            values_right = [(group_right, entry) for entry in mappings_right]

        for gl, ml in values_left:
            for gr, mr in values_right:
                self.add_mapping(gl, ml, gr, mr)

        return values_left + values_right

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

    def num_entries_repr(self) -> str:
        return f"{len(self)} mappings ({self.num_entries_groups_str()})"

    def get_all_mapping_for_groups(
        self, group_left: str, group_right: str
    ) -> List[Tuple[List[str], List[str]]]:
        result = []
        for entry in self.values():
            combinations = entry.get_group_combination(group_left, group_right)
            if combinations is not None:
                result.append(combinations)
        return result

    @classmethod
    def read_json(cls, *args, **kwargs):
        result = super().read_json(*args, **kwargs)
        logger.info("read %s", result.num_entries_repr())
        return result

    def write_json(self, *args, **kwargs) -> None:
        logger.info("write %s", self.num_entries_repr())
        super().write_json(*args, **kwargs)
