import json
import logging
from typing import Dict, List
from uuid import uuid4

from napkon_string_matching.types.base.readable_json import ReadableJson
from napkon_string_matching.types.base.writable_json import WritableJson

logger = logging.getLogger(__name__)


class MappingTarget:
    def __init__(self, data: Dict[str, str] = None) -> None:
        self._data: Dict[str, str] = data if data else {}

    def __getitem__(self, item) -> str:
        return self._data[item]

    def __setitem__(self, item, value) -> None:
        self._data[item] = value

    def dict(self) -> Dict[str, str]:
        return self._data

    def __repr__(self) -> str:
        return f"MappingTarget({repr(self._data)})"

    def __str__(self) -> str:
        return str(self._data)

    def update(self, other) -> None:
        self._data.update(other._data)

    def sources(self) -> List[str]:
        return list(self._data.keys())

    def targets(self) -> List[str]:
        return list(self._data.values())

    def __len__(self) -> int:
        return len(self._data)


class MappingSource:
    __items__ = ["hap", "gecco", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, str]] = None) -> None:
        for item in self.__items__:
            if data and item in data:
                self[item] = MappingTarget(data[item])
            else:
                self[item] = MappingTarget()

    def __getitem__(self, item) -> MappingTarget:
        if item not in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item not in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in self.__items__}

    def _repr_helper(self) -> str:
        return ",".join({f"{item}={repr(self[item])}" for item in self.__items__})

    def __repr__(self) -> str:
        return f"MappingSource({self._repr_helper()})"

    def __str__(self) -> str:
        return f"({self._repr_helper})"

    def __len__(self) -> int:
        return sum([len(self[item]) for item in self.__items__])

    def update(self, other) -> None:
        for item in self.__items__:
            self[item].update(other[item])


class HapMappingSource(MappingSource):
    __items__ = ["gecco", "pop", "suep"]


class PopMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "suep"]


class SuepMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "pop"]


class Mapping(ReadableJson, WritableJson):
    __items__ = ["hap", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, Dict[str, str]]] = None) -> None:
        self.hap: MappingSource = None
        self.pop: MappingSource = None
        self.suep: MappingSource = None

        class_map = {
            "hap": HapMappingSource,
            "pop": PopMappingSource,
            "suep": SuepMappingSource,
        }

        for item in self.__items__:
            if data and item in data:
                self[item] = class_map[item](data[item])
            else:
                self[item] = class_map[item]()

    def __getitem__(self, item) -> MappingSource:
        if item not in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item not in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in Mapping.__items__}

    def __repr__(self) -> str:
        return f"Mapping({','.join({f'{item}={repr(self[item])}' for item in Mapping.__items__})})"

    def __str__(self) -> str:
        return f"({','.join({f'{item}={str(self[item])}' for item in Mapping.__items__})})"

    def update(self, other) -> None:
        for item in self.__items__:
            self[item].update(other[item])

    @classmethod
    def read_json(cls, *args, **kwargs):
        result = super().read_json(*args, **kwargs)
        logger.info(
            "mappings for HAP: %i, POP: %i, SÜP: %i",
            len(result.hap),
            len(result.pop),
            len(result.suep),
        )
        return result

    def write_json(self, *args, **kwargs) -> None:
        logger.info(
            "write mappings for HAP: %i, POP: %i, SÜP: %i",
            len(self.hap),
            len(self.pop),
            len(self.suep),
        )
        super().write_json(*args, **kwargs)

    def to_json(self, indent: int | None = None, *args, **kwargs):
        return json.dumps(self.dict(), indent=indent)

    def __len__(self) -> int:
        return len(self.hap) + len(self.pop) + len(self.suep)

    def to_new(self):
        result = MappingList()
        for first_group, value in self.dict().items():
            for second_group, value in value.items():
                for first_identifier, second_identifier in value.items():
                    result.add_mapping(
                        first_group, first_identifier, second_group, second_identifier
                    )
        return result


class MappingEntry:
    def __init__(self, data: Dict[str, List[str]] | None = None) -> None:
        self._mappings: Dict[str, List[str]] = data if data is not None else {}

    def __getitem__(self, group_name: str) -> List[str] | None:
        return self._mappings.get(group_name)

    def __setitem__(self, group_name: str, value: List[str]) -> None:
        self._mappings[group_name] = value

    def has(self, group_name: str, identifier: str) -> bool:
        return identifier in group if (group := self[group_name]) is not None else False

    def add(self, group_name: str, identifier: str) -> None:
        if (group := self[group_name]) is None:
            self[group_name] = [identifier]
        else:
            group.append(identifier)

    def dict(self) -> Dict[str, List[str]]:
        return self._mappings


class MappingList(ReadableJson, WritableJson):
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
    ) -> None:
        if (mapping := self.mapping_for_identifier(first_group, first_identifier)) is not None:
            mapping.add(second_group, second_identifier)
        else:
            self.set_group(
                uuid4().hex,
                MappingEntry(
                    data={first_group: [first_identifier], second_group: [second_identifier]}
                ),
            )

    def dict(self) -> Dict[str, Dict[str, List[str]]]:
        return {key: mapping.dict() for key, mapping in self._mappings.items()}

    def to_json(self, indent: int | None = None, *args, **kwargs):
        return json.dumps(self.dict(), indent=indent)
