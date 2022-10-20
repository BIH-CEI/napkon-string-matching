import logging
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List

import napkon_string_matching.compare.score_functions
import nltk
import pandas as pd
from napkon_string_matching.types.comparable import COLUMN_NAMES, Columns, Comparable
from napkon_string_matching.types.data import Data, gen_hash
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"
CACHE_FILE_PATTERN = "cache/compared__score_{}.json"

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
        return list(
            set([subentry for entry in self._data[self.__category_column__] for subentry in entry])
        )

    def get_category(self, category: str) -> __category_type__:
        return self.__category_type__(self._data, category)

    def get_without_category(self) -> __category_type__:
        return self.__category_type__(self._data, None)

    def _hash_compare_args(self, other, *args, **kwargs) -> str:
        hashes = [self.hash(), other.hash()]

        hashes += [gen_hash(str(arg)) for arg in args]
        hashes += [gen_hash(str(kwargs)) for kwargs in kwargs.items()]

        return "".join(hashes)

    def compare(
        self,
        other,
        left_existing_mappings: List[str],
        right_existing_mappings: List[str],
        compare_column: str,
        score_threshold: float = 0.1,
        cached: bool = True,
        cache_threshold: float = None,
        *args,
        **kwargs,
    ) -> Comparable:

        # Get the compare dataframe that holds the score to match all entries from
        # the left with each from right dataset
        df_hash = self._hash_compare_args(
            other, left_existing_mappings, right_existing_mappings, compare_column, cache_threshold
        )
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
                left_existing_mappings,
                right_existing_mappings,
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
        left_existing_mappings: List[str],
        right_existing_mappings: List[str],
        score_func: str,
        compare_column: str,
        score_threshold: float = 0.1,
        left_name: str = None,
        right_name: str = None,
        *args,
        **kwargs,
    ) -> Comparable:
        score_func = getattr(napkon_string_matching.compare.score_functions, score_func)

        left = self.dropna(subset=[compare_column])
        right = right.dropna(subset=[compare_column])

        # Remove existing mappings
        left.remove_existing_mappings(left_existing_mappings)
        right.remove_existing_mappings(right_existing_mappings)

        left.map_for_comparable()
        right.map_for_comparable()

        left_prefix = left_name.title()
        right_prefix = right_name.title()

        left = left.add_prefix(left_prefix)
        right = right.add_prefix(right_prefix)
        compare_df = left.merge(right, how="cross")

        logger.info("calculate score")
        comparable = Comparable(data=compare_df, left_name=left_prefix, right_name=right_prefix)

        comparable.match_score = [
            score_func(param, match_param)
            for param, match_param in tqdm(
                zip(
                    comparable[left_prefix + compare_column],
                    comparable[right_prefix + compare_column],
                ),
                total=len(comparable),
            )
        ]

        # Remove not needed columns
        logger.debug("remove superfluous columns")
        columns = [
            prefix + column for prefix in [left_prefix, right_prefix] for column in COLUMN_NAMES
        ]
        columns.append(Columns.MATCH_SCORE.value)
        comparable.drop_superfluous_columns(columns)

        logger.debug("apply score threshold")
        comparable = comparable[comparable.match_score >= score_threshold]
        logger.debug("got %i entries", len(comparable))

        return comparable

    def remove_existing_mappings(self, existing_mappings) -> None:
        self._data = self._data[
            [
                variable not in existing_mappings
                for variable in self[ComparableColumns.IDENTIFIER.value]
            ]
        ]

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
        tokens: Dict = None,
        filter_column: str = None,
        filter_prefix: str = None,
        table_categories: Dict[str, List[str]] | None = None,
        use_cache=True,
        *args,
        **kwargs,
    ):
        """
        Reads a questionnaire from file. If `calculate_tokens == True` tokens are also generated
        using the provided preparator.
        """
        if tokens is None:
            tokens = {}

        file = Path(file_name)
        logger.info(f"prepare file {file.name}")

        output_dir = Path("cache")

        # Build output file pattern
        file_pattern = ["prepared_", file.stem]

        if filter_column and filter_prefix:
            file_pattern.append(filter_column)
            file_pattern.append(filter_prefix)

        if "score_threshold" in tokens:
            file_pattern.append(str(tokens["score_threshold"]))

        file_pattern.append("{}.json")

        file_pattern = "_".join(file_pattern)

        # File names for all cache files
        # Order here is unprocessed -> terms -> prepared
        unprocessed_file = output_dir / f"input__{file.stem}.json"
        terms_file = output_dir / file_pattern.format("terms")
        prepared_file = output_dir / file_pattern.format("prepared")

        # Create output director if not existing
        if use_cache and not output_dir.exists():
            output_dir.mkdir(parents=True)

        data = cls._get_prepared_data(
            file=file,
            prepared_file=prepared_file,
            terms_file=terms_file,
            unprocessed_file=unprocessed_file,
            tokens=tokens,
            preparator=preparator,
            use_cache=use_cache,
            calculate_tokens=calculate_tokens,
            table_categories=table_categories,
            *args,
            **kwargs,
        )
        return data

    @classmethod
    def _get_prepared_data(
        cls,
        prepared_file: Path,
        preparator,
        tokens: Dict,
        use_cache: bool = True,
        calculate_tokens: bool = False,
        *args,
        **kwargs,
    ):
        if use_cache and prepared_file.exists():
            logger.info("using previously cached prepared file")
            return cls.read_json(prepared_file)

        data = cls._get_terms_data(use_cache=use_cache, *args, **kwargs)
        if calculate_tokens:
            config = {"score_threshold": 0.9, "timeout": 30, **tokens}
            preparator.add_tokens(data, **config)
            if use_cache:
                data.write_json(prepared_file)
            data.write_csv(prepared_file.with_suffix(".csv"))
        return data

    @classmethod
    def _get_terms_data(
        cls,
        terms_file: Path,
        filter_column: str = None,
        filter_prefix: str = None,
        use_cache: bool = True,
        *args,
        **kwargs,
    ):
        # If term file exists read its data
        if use_cache and terms_file.exists():
            logger.info("using previously cached terms file")
            return cls.read_json(terms_file)

        data = cls._get_unprocessed_file(use_cache=use_cache, *args, **kwargs)

        if filter_column and filter_prefix:
            data.filter(filter_column, filter_prefix)

        # No matter if unprocessed data was read from cache or dataset file,
        # the terms still needs to be generated
        data.add_terms()
        if use_cache:
            data.write_json(terms_file)
        return data

    @classmethod
    def _get_unprocessed_file(
        cls, unprocessed_file: Path, file: str, use_cache: bool = True, *args, **kwargs
    ):
        if use_cache and unprocessed_file.exists():
            logger.info("using previously cached unprocessed file")
            return cls.read_json(unprocessed_file)

        data = cls.read_original_format(file_name=file, *args, **kwargs)

        if data is None:
            return None

        if use_cache:
            data.write_json(unprocessed_file)
        return data

    def filter(self, filter_column: str, filter_prefix: str):
        before_len = len(self)
        self.drop(
            self[
                [
                    not entry.startswith(filter_prefix) if pd.notna(entry) else False
                    for entry in self[filter_column]
                ]
            ].index,
            inplace=True,
        )
        logger.debug("filtered %i entries", before_len - len(self))
