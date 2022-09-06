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


class MappingSource:
    __items__ = ["hap", "gecco", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, str]] = None) -> None:
        self.hap: MappingTarget = None
        self.gecco: MappingTarget = None
        self.pop: MappingTarget = None
        self.suep: MappingTarget = None

        if data:
            for item, data_ in data.items():
                self[item] = MappingTarget(data_)
        else:
            self.hap = MappingTarget()
            self.gecco = MappingTarget()
            self.pop = MappingTarget()
            self.suep = MappingTarget()

    def __getitem__(self, item) -> MappingTarget:
        if item in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item in MappingSource.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in MappingSource.__items__}


class Mapping:
    __items__ = ["hap", "pop", "suep"]

    def __init__(self, data: Dict[str, Dict[str, Dict[str, str]]]) -> None:
        self.hap: MappingSource = None
        self.pop: MappingSource = None
        self.suep: MappingSource = None

        if data:
            for item, data_ in data.items():
                self[item] = MappingSource(data_)
        else:
            self.hap = MappingSource()
            self.pop = MappingSource()
            self.suep = MappingSource()

    def __getitem__(self, item) -> MappingSource:
        if item in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        return getattr(self, item)

    def __setitem__(self, item, value) -> None:
        if item in Mapping.__items__:
            raise ValueError(f"item not found: {item}")
        setattr(self, item, value)

    def dict(self) -> Dict[str, Dict[str, str]]:
        return {item: self[item].dict() for item in MappingSource.__items__}
