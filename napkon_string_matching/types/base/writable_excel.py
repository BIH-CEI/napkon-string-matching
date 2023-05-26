import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class WritableExcel:
    def write_excel(self, file: str):
        """
        Write data to file in EXCEL format

        Attributes
        ---
            file_path (str|Path):   file path to write to
        """
        path = Path(file)
        if not path.parent.exists():
            path.parent.mkdir(parents=True)

        logger.info("write result to file %s", str(file))
        writer = pd.ExcelWriter(file, engine="openpyxl")
        for name, comp in self.get_items():
            comp.to_excel(writer, sheet_name=name, index=False)
        writer.save()
        logger.info("...done")

    def get_items(self) -> List[Tuple[str, pd.DataFrame]]:
        raise NotImplementedError()
