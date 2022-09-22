TABLE_SEPARATOR = ":"
IDENTIFIER_SEPARATOR = "#"


def generate_id(*args) -> str:
    return IDENTIFIER_SEPARATOR.join([str(arg) for arg in args if arg]).replace(" ", "-")
