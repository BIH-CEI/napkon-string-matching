from pathlib import Path

from napkon_string_matching.types.readable_json import ReadableJson


class ReadableJsonFrame(ReadableJson):
    @classmethod
    def read_json(cls, file_name: str | Path, *args, **kwargs):
        """
        Read dataframe data stored as JSON from file

        Attributes
        ---
            file_path (str|Path):   file path to read from

        Returns
        ---
            Self:  from the file contents
        """

        result = super().read_json(file_name, *args, **kwargs)
        result.reset_index(drop=True, inplace=True)
        return result
