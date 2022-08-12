from typing import List

import pandas as pd
from napkon_string_matching.terminology.constants import CONFIG_FIELD_MESH
from napkon_string_matching.terminology.mesh import MeshProvider

from .provider_base import ProviderBase


class TerminologyProvider:
    def __init__(self, config) -> None:
        self.config = config

        self.providers: List[ProviderBase] = []
        self.providers.append(MeshProvider(self.config[CONFIG_FIELD_MESH]))

    @property
    def initialized(self) -> bool:
        return all([provider.initialized for provider in self.providers])

    def initialize(self) -> None:
        if not self.initialized:
            for provider in self.providers:
                provider.initialize()

    @property
    def headings(self) -> pd.DataFrame:
        results = [provider.headings for provider in self.providers]
        return pd.concat(results)

    @property
    def synonyms(self) -> pd.DataFrame:
        results = [provider.synonyms for provider in self.providers]
        return pd.concat(results)
