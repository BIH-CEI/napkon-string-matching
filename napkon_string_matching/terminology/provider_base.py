from abc import ABC, abstractmethod

import pandas as pd


class ProviderBase(ABC):
    def __init__(self) -> None:
        self._headings = None
        self._synonyms = None

    @property
    def initialized(self) -> bool:
        return self._synonyms is not None and self._headings is not None

    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError()

    @property
    def headings(self) -> pd.DataFrame:
        return self._headings

    @property
    def synonyms(self) -> pd.DataFrame:
        return self._synonyms
