from typing import Dict


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


class MappingSource:
    __items__ = ["hap", "gecco", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, str]] = None) -> None:
        if data:
            for item, data_ in data.items():
                self[item] = MappingTarget(data_)
        else:
            for item in self.__items__:
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


class HapMappingSource(MappingSource):
    __items__ = ["gecco", "pop", "suep"]


class PopMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "suep"]


class SuepMappingSource(MappingSource):
    __items__ = ["gecco", "hap", "pop"]


class Mapping:
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

        if data:
            for item, data_ in data.items():
                self[item] = class_map[item](data_)
        else:
            for item in self.__items__:
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
