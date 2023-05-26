from pathlib import Path

from napkon_string_matching.types.gecco_definition import GeccoDefinition
from napkon_string_matching.types.gecco_definition_types.gecco83 import \
    Gecco83Definition
from napkon_string_matching.types.gecco_definition_types.geccoplus import \
    GeccoPlusDefinition


class GeccoCombinedDefinition(Gecco83Definition, GeccoPlusDefinition):
    """
    Class that can read definitions for GECCO83 and GECCOplus
    """

    @staticmethod
    def read_original_format(
        gecco83_file: str | Path,
        geccoplus_file: str | Path,
        file_name: str | Path | None = None,
        *args,
        **kwargs
    ):
        if file_name is not None and Path(file_name).exists():
            return GeccoDefinition.read_original_format(file_name)
        gecco = Gecco83Definition.read_original_format(gecco83_file)
        geccoplus = GeccoPlusDefinition.read_original_format(geccoplus_file)
        result: GeccoDefinition = gecco.concat(geccoplus)
        if file_name is not None:
            result.write_json(file_name)

        result._extend_parameters()
        return result
