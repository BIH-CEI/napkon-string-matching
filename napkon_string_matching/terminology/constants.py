if __package__ == "":
    from table_request import TableRequest
else:
    from .table_request import TableRequest


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
