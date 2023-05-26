from typing import List, Tuple

import pandas as pd

from napkon_string_matching.terminology.mesh import MeshProvider
from napkon_string_matching.terminology.provider_base import ProviderBase

CONFIG_FIELD_MESH = "mesh"


class TerminologyProvider:
    """
    Provides combined information from different termonologies
    """
    def __init__(self, config) -> None:
        """
        A terminology provider, that holds muliple providers for different terminologies.
        The providers are initialized from the config.
        """
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

    def get_matches(
        self,
        term: List[str],
        score_threshold: float = 0.1,
    ) -> List[Tuple[str, str, float]] | None:
        """
        Get matches for `term` from different terminologies
        """
        results = []
        for provider in self.providers:
            results += provider.get_matches(term, score_threshold)
        return results if results else None
