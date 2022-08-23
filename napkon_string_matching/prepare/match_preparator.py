import logging
from multiprocessing import Pool
from typing import List

from napkon_string_matching.prepare.generate import gen_term
from napkon_string_matching.terminology.mesh import (
    TERMINOLOGY_REQUEST_HEADINGS,
    TERMINOLOGY_REQUEST_TERMS,
    TableRequest,
)
from napkon_string_matching.terminology.provider import TerminologyProvider
from napkon_string_matching.types.questionnaire import Questionnaire
from tqdm import tqdm

CONFIG_FIELD_TERMINOLOGY = "terminology"


logger = logging.getLogger(__name__)


class MatchPreparator:
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

    def add_terms(self, qn: Questionnaire, language: str = "german"):
        logger.info("add terms...")
        result = [
            gen_term(category, question, item, language)
            for category, question, item in zip(qn.categories, qn.question, qn.item)
        ]
        qn.term = result
        logger.info("...done")

    def add_tokens(
        self, qn: Questionnaire, score_threshold: float = 0.1, verbose: bool = True, timeout=10
    ):
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
                for term in qn.term
            ]

            if verbose:
                results = [res.get(timeout=timeout) for res in tqdm(multiple_results)]
            else:
                results = [res.get(timeout=timeout) for res in multiple_results]

        unpacked = [tuple(zip(*entry)) if entry else (None, None, None) for entry in results]

        qn.token_ids = [ids if ids else None for ids, *_ in unpacked]
        qn.tokens = [tokens if tokens else None for _, tokens, *_ in unpacked]
        qn.token_match = results
        logger.info("...done")
