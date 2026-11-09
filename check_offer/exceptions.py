class ContractError(Exception):
    """The analysis written by the agent does not follow the expected format."""


class InputError(Exception):
    """An input file is missing, unreadable or in an unsupported format."""
