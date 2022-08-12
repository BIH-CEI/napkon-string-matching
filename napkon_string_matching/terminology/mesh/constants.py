from napkon_string_matching.terminology.mesh.table_request import TableRequest

CONFIG_FIELD_DB = "db"

TERMINOLOGY_COLUMN_TERM = "Term"
TERMINOLOGY_COLUMN_ID = "Id"

TERMINOLOGY_REQUEST_TERMS = [
    TableRequest(
        table_name="EntryTerms",
        id_column="MainHeadingsId",
        term_column="DescriptionGerman",
    ),
    TableRequest(
        table_name="MainHeadings",
        id_column="Id",
        term_column="DescriptionGerman",
    ),
]


TERMINOLOGY_REQUEST_HEADINGS = [
    TableRequest(
        table_name="MainHeadings",
        id_column="Id",
        term_column="DescriptionGerman",
    ),
]
