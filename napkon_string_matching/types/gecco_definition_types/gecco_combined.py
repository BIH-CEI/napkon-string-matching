from pathlib import Path

from napkon_string_matching.types.gecco_definition_types.gecco83 import Gecco83Definition
from napkon_string_matching.types.gecco_definition_types.geccoplus import GeccoPlusDefinition


class GeccoCombinedDefinition(Gecco83Definition, GeccoPlusDefinition):
    @staticmethod
    def read_original_format(gecco83_file: str | Path, geccoplus_file: str | Path, *args, **kwargs):
        gecco = Gecco83Definition.read_original_format(gecco83_file)
        geccoplus = GeccoPlusDefinition.read_original_format(geccoplus_file)
        return gecco.concat(geccoplus)
