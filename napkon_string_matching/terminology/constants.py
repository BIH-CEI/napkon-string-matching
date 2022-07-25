from napkon_string_matching.terminology.table_request import TableRequest

COLUMN_TERM = "Term"
COLUMN_ID = "Id"

REQUEST_TERMS = [
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


REQUEST_HEADINGS = [
    TableRequest(
        table_name="MainHeadings",
        id_column="Id",
        term_column="DescriptionGerman",
    ),
]
