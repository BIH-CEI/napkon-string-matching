import logging
from multiprocessing import Pool
from typing import List

import pandas as pd
from napkon_string_matching.constants import (
    DATA_COLUMN_CATEGORIES,
    DATA_COLUMN_ITEM,
    DATA_COLUMN_QUESTION,
    DATA_COLUMN_TERM,
    DATA_COLUMN_TOKEN_IDS,
    DATA_COLUMN_TOKEN_MATCH,
    DATA_COLUMN_TOKENS,
)
from napkon_string_matching.prepare.generate import gen_term, gen_tokens
from napkon_string_matching.terminology import (
    TERMINOLOGY_REQUEST_HEADINGS,
    TERMINOLOGY_REQUEST_TERMS,
    PostgresMeshConnector,
    TableRequest,
)
from tqdm import tqdm

logger = logging.getLogger(__name__)


class MatchPreparator:
    def __init__(
        self,
        dbConfig: dict,
        term_requests: List[TableRequest] = TERMINOLOGY_REQUEST_TERMS,
        heading_requests: List[TableRequest] = TERMINOLOGY_REQUEST_HEADINGS,
    ):
        self.dbConfig = dbConfig
        self.term_requests = term_requests
        self.heading_requests = heading_requests
        self.terms = None
        self.headings = None

    def load_terms(self):
        if not self.terms or not self.headings:
            logger.info("load terms from database...")
            with PostgresMeshConnector(**self.dbConfig) as connector:
                logger.info("...load MeSH terms...")
                self.terms = connector.read_tables(self.term_requests)
                self.headings = connector.read_tables(self.heading_requests)
            logger.info(
                "...got %i headings and %i total terms",
                len(self.headings),
                len(self.terms),
            )

    def add_terms(self, df: pd.DataFrame, language: str = "german"):
        logger.info("add terms...")
        result = [
            gen_term(category, question, item, language)
            for category, question, item in zip(
                df[DATA_COLUMN_CATEGORIES],
                df[DATA_COLUMN_QUESTION],
                df[DATA_COLUMN_ITEM],
            )
        ]
        df[DATA_COLUMN_TERM] = result
        logger.info("...done")

    def add_tokens(
        self, df: pd.DataFrame, score_threshold: int, verbose: bool = True, timeout=10
    ):
        self.load_terms()

        if self.terms is None or self.headings is None:
            raise RuntimeError("'terms' and/or 'headings' not initialized")

        logger.info("add tokens...")

        # Generate the tokens using multiple processes to reduce computational time
        with Pool() as pool:
            multiple_results = [
                pool.apply_async(
                    gen_tokens, (term, self.terms, self.headings, score_threshold)
                )
                for term in df[DATA_COLUMN_TERM]
            ]

            if verbose:
                result = [res.get(timeout=timeout) for res in tqdm(multiple_results)]
            else:
                result = [res.get(timeout=timeout) for res in multiple_results]

        df[DATA_COLUMN_TOKENS] = [tokens if tokens else None for tokens, _, _ in result]
        df[DATA_COLUMN_TOKEN_IDS] = [ids if ids else None for _, ids, _ in result]
        df[DATA_COLUMN_TOKEN_MATCH] = [
            match if match else None for _, _, match in result
        ]
        logger.info("...done")
