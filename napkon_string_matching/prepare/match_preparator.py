import logging
from multiprocessing import Pool
from typing import List

from tqdm import tqdm

from napkon_string_matching.terminology.mesh import (
    TERMINOLOGY_REQUEST_HEADINGS, TERMINOLOGY_REQUEST_TERMS, TableRequest)
from napkon_string_matching.terminology.provider import TerminologyProvider
from napkon_string_matching.types.comparable_data import ComparableData

CONFIG_FIELD_TERMINOLOGY = "terminology"


logger = logging.getLogger(__name__)


class MatchPreparator:
    """
    Prepares data for the matching process
    """
    def __init__(
        self,
        config: dict,
        term_requests: List[TableRequest] = TERMINOLOGY_REQUEST_TERMS,
        heading_requests: List[TableRequest] = TERMINOLOGY_REQUEST_HEADINGS,
    ):
        self.config = config
        self.term_requests = term_requests
        self.heading_requests = heading_requests

        self.terminology_provider = TerminologyProvider(self.config[CONFIG_FIELD_TERMINOLOGY])

    def add_tokens(
        self,
        cs: ComparableData,
        score_threshold: float = 0.1,
        verbose: bool = True,
        timeout=10,
    ):
        """
        Add generate token matches for `cs` entries using `TherminologyProviders`
        configured in the config file. `score_threshold` sets the minimum threshold
        that a match needs to have.
        """
        if not self.terminology_provider.initialized:
            self.terminology_provider.initialize()

        if not self.terminology_provider.initialized:
            raise RuntimeError("'terms' and/or 'headings' not initialized")

        logger.info("add tokens...")

        # Generate the tokens using multiple processes to reduce computational time
        with Pool() as pool:
            multiple_results = [
                pool.apply_async(
                    self.terminology_provider.get_matches,
                    (term, score_threshold),
                )
                for term in cs.term
            ]

            if verbose:
                results = [res.get(timeout=timeout) for res in tqdm(multiple_results)]
            else:
                results = [res.get(timeout=timeout) for res in multiple_results]

        unpacked = [tuple(zip(*entry)) if entry else (None, None, None) for entry in results]

        cs.token_ids = [ids if ids else None for ids, *_ in unpacked]
        cs.tokens = [tokens if tokens else None for _, tokens, *_ in unpacked]
        cs.token_match = results
        logger.info("...done")
