from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class TableRequest:
    """
    Specifies how to address/extract data from the database
    """

    table_name: str
    """Name of the table to access"""

    id_column: str
    """Name of the column to use as an identifier"""

    term_column: str
    """Name of the column to use a the term"""
