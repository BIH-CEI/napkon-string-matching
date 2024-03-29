import logging
from abc import abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from tqdm import tqdm

import napkon_string_matching.compare.score_functions
from napkon_string_matching.types.comparable import (COLUMN_NAMES,
                                                     QUESTION_OUTPUT, Columns,
                                                     Comparable)
from napkon_string_matching.types.data import Data, gen_hash
from napkon_string_matching.types.mapping import Mapping

nltk.download("punkt")
nltk.download("stopwords")


PREPARE_REMOVE_SYMBOLS = "!?,.()[]:;*"
CACHE_FILE_PATTERN = "compared__score_{}.json"

COMP_COLUMN = "Compare"

logger = logging.getLogger(__name__)


class ComparableColumns(Enum):
    TERM = "Term"
    TOKENS = "Tokens"
    TOKEN_IDS = "TokenIds"
    TOKEN_MATCH = "TokenMatch"
    MATCHES = "Matches"
    IDENTIFIER = "Identifier"


class ComparableData(Data):
    """
    Class that allows to compare different types of data. This data can be derived from Datensatztabellen or GECCO definitions by inheriting this class.
    """
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
        strings = [self.to_csv(), other.to_csv()]

        strings += [str(arg) for arg in args]
        strings += [str(kwargs) for kwargs in kwargs.items()]

        return gen_hash("".join(strings))

    def compare(
        self,
        other,
        existing_mappings_whitelist: Mapping,
        existing_mappings_blacklist: Mapping,
        compare_column: str,
        score_threshold: float = 0.1,
        cached: bool = True,
        cache_threshold: float = None,
        cache_dir: str | Path | None = None,
        identifier_column_left: str | None = None,
        identifier_column_right: str | None = None,
        *args,
        **kwargs,
    ) -> Comparable:

        # Get the compare dataframe that holds the score to match all entries from
        # the left with each from right dataset
        df_hash = self._hash_compare_args(
            other=other,
            existing_mappings_whitelist=existing_mappings_whitelist,
            existing_mappings_blacklist=existing_mappings_blacklist,
            compare_column=compare_column,
            cache_threshold=cache_threshold,
        )
        cache_dir = Path(cache_dir if cache_dir else "cache")
        cache_score_file = cache_dir / CACHE_FILE_PATTERN.format(df_hash)
        logger.debug("cache hash %s", df_hash)

        if cache_score_file.exists() and cached:
            logger.info("using cached result")
            result = Comparable.read_json(cache_score_file)
        else:
            if not cache_threshold:
                cache_threshold = score_threshold
            result = self.gen_comparable(
                other,
                existing_mappings_whitelist=existing_mappings_whitelist,
                existing_mappings_blacklist=existing_mappings_blacklist,
                score_threshold=cache_threshold,
                compare_column=compare_column,
                identifier_column_left=identifier_column_left,
                identifier_column_right=identifier_column_right,
                *args,
                **kwargs,
            )

            if not cache_score_file.parent.exists():
                cache_score_file.parent.mkdir(parents=True)

            logger.info("write cache to file")
            result.write_json(cache_score_file)

        # Filter outside of the caching to reuse same cache with different thresholds
        result = result[result.match_score >= score_threshold]
        logger.info("got %i filtered entries", len(result))

        result.sort_by_score()

        return result

    def map_for_comparable(self) -> pd.DataFrame:
        return self.rename(columns=self.__column_mapping__)

    def gen_comparable(
        self,
        right,
        existing_mappings_whitelist: Mapping,
        existing_mappings_blacklist: Mapping,
        score_func: str,
        compare_column: str,
        category_column: str = "Category",
        score_threshold: float = 0.1,
        left_name: str = None,
        right_name: str = None,
        filter_categories: bool = False,
        identifier_column_left: str | None = None,
        identifier_column_right: str | None = None,
        *args,
        **kwargs,
    ) -> Comparable:
        score_func = getattr(napkon_string_matching.compare.score_functions, score_func)

        left = self.dropna(subset=[compare_column])
        right = right.dropna(subset=[compare_column])
        logger.info(
            "comparing number of items %i left, %i right, potential %s comparisons",
            len(left),
            len(right),
            "{:,}".format(len(left) * len(right)),
        )

        # Remove existing whitelisted mappings
        remove_existing_mappings(
            left,
            right,
            left_name,
            right_name,
            existing_mappings_whitelist,
        )
        logger.info(
            "after removing existing whitelisted mappings: %i left, %i right", len(left), len(right)
        )

        left = left.map_for_comparable()
        right = right.map_for_comparable()

        left[COMP_COLUMN] = [self.gen_comp_value(item) for item in left[compare_column]]
        right[COMP_COLUMN] = [self.gen_comp_value(item) for item in right[compare_column]]

        left[QUESTION_OUTPUT] = [
            ":".join(flatten_list(item)) for item in left[ComparableColumns.TERM.value]
        ]
        right[QUESTION_OUTPUT] = [
            ":".join(flatten_list(item)) for item in right[ComparableColumns.TERM.value]
        ]

        left_prefix = left_name.title()
        right_prefix = right_name.title()

        left = left.add_prefix(left_prefix)
        right = right.add_prefix(right_prefix)
        compare_df = left.merge(right, how="cross")
        logger.info("generated %s combination for comparision", "{:,}".format(len(compare_df)))

        # Remove blacklisted comparisions
        compare_df = remove_existing_mapping_from_df(
            compare_df,
            left_name,
            right_name,
            left_prefix,
            right_prefix,
            existing_mappings_blacklist,
            identifier_column_right=identifier_column_right,
            identifier_column_left=identifier_column_left,
        )
        logger.info(
            "remaining %s entries after removing blacklisted ones", "{:,}".format(len(compare_df))
        )

        if filter_categories:
            previous_length = len(compare_df)
            compare_df = categories_matching(
                compare_df, left_prefix + category_column, right_prefix + category_column
            )
            logger.info(
                "filtered %s entries not matching categories, now %s",
                "{:,}".format(previous_length - len(compare_df)),
                "{:,}".format(len(compare_df)),
            )

        logger.info("calculate score")
        comparable = Comparable(data=compare_df, left_name=left_prefix, right_name=right_prefix)

        comparable.match_score = [
            self.compare_terms(param, match_param, score_func)
            for param, match_param in tqdm(
                zip(
                    comparable[left_prefix + COMP_COLUMN],
                    comparable[right_prefix + COMP_COLUMN],
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

        logger.info("apply score threshold")
        comparable = comparable[comparable.match_score >= score_threshold]
        logger.info("got %s entries", "{:,}".format(len(comparable)))

        return comparable

    @classmethod
    def compare_terms(cls, left: List[str], right: List[str], score_func) -> float:
        """
        Calculate the score in an iterative way. The total score is calculated from the sum of sub-parts
        weightened from most to least specific. Means the most specific score is weightened with 0.5 and
        weight halfens from there on.
        """
        score = 0
        len_left = len(left)
        len_right = len(right)
        left_max = len_left - 1
        right_max = len_right - 1
        factor = 1
        for i in range(1, max(len_left, len_right) + 1):
            score_ = score_func(left[min(i, left_max)], right[min(i, right_max)])
            factor /= 2
            score += score_ * factor
        return score

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
    def gen_term(*items: str) -> List[str]:
        return [item for item in items if item]

    @classmethod
    def gen_comp_value(cls, items: List[str]) -> List[str]:
        return [cls.tokenize(items[-i:]) for i in range(1, len(items) + 1)]

    @staticmethod
    def tokenize(parts: List[str], language: str = "german") -> str:
        token_string = flatten_list(parts)
        tokens = word_tokenize(" ".join(token_string))

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
        cache_dir: str | None = None,
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

        output_dir = Path(cache_dir if cache_dir else "cache")

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

    def get_existing_mapping_ids(self, group_name: str, mappings: Mapping):
        mappings_for_group = mappings.filter_by_group(group_name)
        identifiers = self[Columns.IDENTIFIER.value]
        ids = [
            id
            for id, mapping_identifiers in mappings_for_group.items()
            for identifier in identifiers
            if identifier in mapping_identifiers
        ]
        return list(set(ids))


def categories_matching(df: pd.DataFrame, column_left: str, column_right: str) -> pd.DataFrame:
    first_row = df.iloc[0]
    categories_left, categories_right = first_row[column_left], first_row[column_right]
    if isinstance(categories_left, list):
        if isinstance(categories_right, list):
            matching_func = lambda x, y: (not set(x).isdisjoint(set(y))) or (not x and not y)
        else:
            matching_func = lambda x, y: x in set(y)
    else:
        if isinstance(categories_right, list):
            matching_func = lambda x, y: x in set(y)
        else:
            matching_func = lambda x, y: x == y

    logger.info("filtering categories...")
    return df[
        [
            matching_func(*categories)
            for categories in tqdm(
                zip(
                    df[column_left],
                    df[column_right],
                ),
                total=len(df),
            )
        ]
    ]


def remove_existing_mappings(
    left: ComparableData,
    right: ComparableData,
    left_name: str,
    right_name: str,
    existing_mappings: Mapping,
):
    try:
        left_ids = left.get_existing_mapping_ids(left_name, existing_mappings)
        right_ids = right.get_existing_mapping_ids(right_name, existing_mappings)
    except KeyError:
        return

    used_ids = list(set(left_ids).intersection(right_ids))
    filtered_mappings = existing_mappings.get_filtered(used_ids)

    remove_identifiers = get_identifiers_from_mapping(filtered_mappings, left_name)
    left.remove_existing_mappings(remove_identifiers)

    remove_identifiers = get_identifiers_from_mapping(filtered_mappings, right_name)
    right.remove_existing_mappings(remove_identifiers)


def get_identifiers_from_mapping(mappings: Mapping, group: str) -> List[str]:
    result = []
    for groups in mappings.values():
        result += groups[group]
    return result


def remove_existing_mapping_from_df(
    df: pd.DataFrame,
    left_name: str,
    right_name: str,
    left_prefix: str,
    right_prefix: str,
    existing_mappings: Mapping,
    identifier_column_left: str | None = None,
    identifier_column_right: str | None = None,
):
    logger.info("remove black-listed entries...")
    group_mappings_flat = flatten_mapping(left_name, right_name, existing_mappings)

    if not identifier_column_left:
        identifier_column_left = Columns.IDENTIFIER.value
    if not identifier_column_right:
        identifier_column_right = Columns.IDENTIFIER.value

    # Calculate entries to return
    maintain_rows = [
        (left, right) not in group_mappings_flat
        for left, right in tqdm(
            zip(
                df[left_prefix + identifier_column_left],
                df[right_prefix + identifier_column_right],
            ),
            total=len(df),
        )
    ]
    return df[maintain_rows]


def flatten_mapping(left_group: str, right_group: str, mapping: Mapping) -> List[Tuple[str, str]]:
    group_mappings = mapping.get_all_mapping_for_groups(left_group, right_group)

    group_mappings_flat = []
    for left_list, right_list in group_mappings:
        for left_entry in left_list:
            for right_entry in right_list:
                group_mappings_flat.append((left_entry, right_entry))

    return group_mappings_flat


def flatten_list(list_) -> List[str]:
    result = []
    for part in list_:
        if isinstance(part, List):
            result += part
        else:
            result.append(part)
    return result
