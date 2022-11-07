import json
import logging
from pathlib import Path
from typing import List

import requests

from napkon_string_matching.types.kds_definition import KdsDefinition
from napkon_string_matching.types.kds_definition_types.fhir import FhirKdsDefinition

logger = logging.getLogger(__name__)


class SimplifierKdsDefinition(KdsDefinition):
    @classmethod
    def read_original_format(cls, file_name: str | Path, modules: List[str], *args, **kwargs):
        if Path(file_name).exists():
            return super().read_original_format(file_name=file_name, *args, **kwargs)

        result = cls()
        with requests.Session() as session:
            for module in modules:
                resp = session.get(module + "/StructureDefinition")
                if resp.status_code != 200:
                    logger.error("failed to get %s: %s", resp.url, resp.text)
                    continue
                bundle = json.loads(resp.text)
                for entry in bundle["entry"]:
                    resource = entry["resource"]
                    if (
                        resource["resourceType"] != "StructureDefinition"
                        or resource.get("kind") != "logical"
                    ):
                        continue
                    definition = FhirKdsDefinition.read_original_format(
                        elements=resource["differential"]["element"]
                    )
                    result = result.concat(definition)
        result.write_json(file_name=file_name)

        return result
