import logging
from abc import abstractmethod
from enum import Enum
from hashlib import md5
from pathlib import Path
from typing import List

import napkon_string_matching.compare.score_functions
import nltk
from napkon_string_matching.types.comparable import Comparable
from napkon_string_matching.types.subscriptable import Subscriptable
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"
CACHE_FILE_PATTERN = "compared/cache_score_{}.json"

logger = logging.getLogger(__name__)


def gen_hash(string: str) -> str:
    return md5(string.encode("utf-8"), usedforsecurity=False).hexdigest()


class ComparableColumns(Enum):
    TERM = "Term"
    TOKENS = "Tokens"
    TOKEN_IDS = "TokenIds"
    TOKEN_MATCH = "TokenMatch"
    MATCHES = "Matches"
    IDENTIFIER = "Identifier"


class ComparableSubscriptable(Subscriptable):
    __slots__ = [column.name.lower() for column in ComparableColumns]
    __column_mapping__ = {}

    @abstractmethod
    def hash(self) -> str:
        raise NotImplementedError()

    def _hash_compare_args(self, other, *args, **kwargs) -> str:
        hashes = [self.hash(), other.hash()]

        hashes += [gen_hash(str(arg)) for arg in args]
        hashes += [gen_hash(str(kwargs)) for kwargs in kwargs.items()]

        return "".join(hashes)

    def compare(
        self,
        other,
        score_threshold: float = 0.1,
        compare_column: str = "",
        cached: bool = True,
        cache_threshold: float = None,
        *args,
        **kwargs,
    ) -> Comparable:

        # Get the compare dataframe that holds the score to match all entries from
        # the left with each from right dataset
        df_hash = self._hash_compare_args(other, *args, **kwargs)
        cache_score_file = Path(CACHE_FILE_PATTERN.format(df_hash))
        logger.debug("cache hash %s", df_hash)

        if cache_score_file.exists() and cached:
            logger.info("using cached result")
            result = Comparable.read_json(cache_score_file)
        else:
            if not cache_threshold:
                cache_threshold = score_threshold
            result = self.gen_comparable(
                other,
                score_threshold=cache_threshold,
                compare_column=compare_column,
                *args,
                **kwargs,
            )

            if not cache_score_file.parent.exists():
                cache_score_file.parent.mkdir(parents=True)

            logger.info("write cache to file")
            result.write_json(cache_score_file)

        # Filter outside of the caching to reuse same cache with different thresholds
        result = result[result.match_score >= score_threshold]
        logger.debug("got %i filtered entries", len(result))

        return result

    def map_for_comparable(self) -> None:
        self.rename(columns=self.__column_mapping__, inplace=True)

    def gen_comparable(
        self,
        right,
        score_func: str,
        score_threshold: float = 0.1,
        compare_column: str = "",
        *args,
        **kwargs,
    ) -> Comparable:
        score_func = getattr(napkon_string_matching.compare.score_functions, score_func)

        left = self.dropna(subset=[compare_column])
        right = right.dropna(subset=[compare_column])

        left.map_for_comparable()
        right.map_for_comparable()

        right = right.add_prefix("Match")
        compare_df = left.merge(right, how="cross").dataframe()

        logger.info("calculate score")
        comparable = Comparable(compare_df)

        comparable.match_score = [
            score_func(param, match_param)
            for param, match_param in tqdm(
                zip(comparable[compare_column], comparable["Match" + compare_column]),
                total=len(comparable),
            )
        ]

        # Remove not needed columns
        comparable.drop_superfluous_columns()

        comparable = comparable[comparable.match_score >= score_threshold]
        logger.debug("got %i entries", len(comparable))

        return comparable

    @abstractmethod
    def add_terms(self, language: str = "german"):
        raise NotImplementedError()

    @staticmethod
    def gen_term(parts: List[str], language: str = "german") -> str:
        tokens = word_tokenize(" ".join(parts))

        stop_words = set(stopwords.words(language))
        tokens = {
            word
            for word in tokens
            if word.casefold() not in stop_words and word not in PREPARE_REMOVE_SYMBOLS
        }

        return sorted(tokens, key=str.casefold)
