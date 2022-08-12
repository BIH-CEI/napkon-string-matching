import logging

from napkon_string_matching.terminology.mesh.constants import (
    CONFIG_FIELD_DB,
    TERMINOLOGY_REQUEST_HEADINGS,
    TERMINOLOGY_REQUEST_TERMS,
)
from napkon_string_matching.terminology.mesh.mesh_connector import PostgresMeshConnector
from napkon_string_matching.terminology.provider_base import ProviderBase

logger = logging.getLogger(__name__)


class MeshProvider(ProviderBase):
    def __init__(self, config) -> None:
        super().__init__()
        self.config = config

        self.term_requests = TERMINOLOGY_REQUEST_TERMS
        self.heading_requests = TERMINOLOGY_REQUEST_HEADINGS

    def initialize(self) -> None:
        if not self.initialized:
            logger.info("load terms from database...")
            with PostgresMeshConnector(**self.config[CONFIG_FIELD_DB]) as connector:
                logger.info("...load MeSH terms...")
                self._synonyms = connector.read_tables(self.term_requests)
                self._headings = connector.read_tables(self.heading_requests)
            logger.info(
                "...got %i headings and %i total synonyms",
                len(self._headings),
                len(self._synonyms),
            )
