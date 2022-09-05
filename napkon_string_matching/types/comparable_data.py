import logging
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import List

import napkon_string_matching.compare.score_functions
import nltk
from napkon_string_matching.types.comparable import Comparable
from napkon_string_matching.types.data import Data, gen_hash
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"
CACHE_FILE_PATTERN = "compared/cache_score_{}.json"

logger = logging.getLogger(__name__)


class ComparableColumns(Enum):
    TERM = "Term"
    TOKENS = "Tokens"
    TOKEN_IDS = "TokenIds"
    TOKEN_MATCH = "TokenMatch"
    MATCHES = "Matches"
    IDENTIFIER = "Identifier"


class ComparableData(Data):
    __slots__ = [column.name.lower() for column in ComparableColumns]
    __column_mapping__ = {}
    __category_type__ = None

    @property
    def categories(self) -> List[str]:
        return list(self._data[self.__category_column__].unique())

    def get_category(self, category: str) -> __category_type__:
        return self.__category_type__(self._data, category)

    def _hash_compare_args(self, other, *args, **kwargs) -> str:
        hashes = [self.hash(), other.hash()]

        hashes += [gen_hash(str(arg)) for arg in args]
        hashes += [gen_hash(str(kwargs)) for kwargs in kwargs.items()]

        return "".join(hashes)

    def compare(
        self,
        other,
        compare_column: str,
        score_threshold: float = 0.1,
        cached: bool = True,
        cache_threshold: float = None,
        *args,
        **kwargs,
    ) -> Comparable:

        # Get the compare dataframe that holds the score to match all entries from
        # the left with each from right dataset
        df_hash = self._hash_compare_args(other, compare_column, cache_threshold)
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

        result.sort_by_score()

        return result

    def map_for_comparable(self) -> None:
        self.rename(columns=self.__column_mapping__, inplace=True)

    def gen_comparable(
        self,
        right,
        score_func: str,
        compare_column: str,
        score_threshold: float = 0.1,
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

    @staticmethod
    def read_original_format(file_name, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def prepare(
        cls,
        file_name: str,
        preparator,
        calculate_tokens: bool = False,
        tokens=dict(),
        *args,
        **kwargs,
    ):
        """
        Reads a questionnaire from file. If `calculate_tokens == True` tokens are also generated
        using the provided preparator.
        """
        file = Path(file_name)
        logger.info(f"prepare file {file.name}")

        output_dir = Path("prepared")

        # Build output file pattern
        file_pattern = [file.stem]

        if "filter_column" in kwargs:
            file_pattern.append(kwargs["filter_column"])

        if "filter_prefix" in kwargs:
            file_pattern.append(kwargs["filter_prefix"])

        if "score_threshold" in tokens:
            file_pattern.append(str(tokens["score_threshold"]))

        file_pattern.append("{}.json")

        file_pattern = "_".join(file_pattern)

        # File names for all cache files
        # Order here is unprocessed -> terms -> prepared
        unprocessed_file = output_dir / file_pattern.format("unprocessed")
        terms_file = output_dir / file_pattern.format("terms")
        prepared_file = output_dir / file_pattern.format("prepared")

        # Create output director if not existing
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # If prepared already exists, read it and return data
        if prepared_file.exists():
            logger.info("using previously cached prepared file")
            data = cls.read_json(prepared_file)
            return data

        # If term file exists read its data
        if terms_file.exists():
            logger.info("using previously cached terms file")
            data = cls.read_json(terms_file)
        else:
            # If unprocessed file exists, read it; otherwise calculate
            if unprocessed_file.exists():
                logger.info("using previously cached unprocessed file")
                data = cls.read_json(unprocessed_file)
            else:
                data = cls.read_original_format(file, *args, **kwargs)

                if data is None:
                    return None

                data.write_json(unprocessed_file)

            # No matter if unprocessed data was read from cache or dataset file,
            # the terms still needs to be generated
            data.add_terms()
            data.write_json(terms_file)

        # No matter if terms data was read or calculated,
        # the tokens still need to be generated if required
        if calculate_tokens:
            config = {"score_threshold": 0.9, "timeout": 30, **tokens}
            preparator.add_tokens(data, **config)
            data.write_json(prepared_file)
            data.write_csv(prepared_file.with_suffix(".csv"))

        return data
