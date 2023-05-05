"""
PDG API exception classes.
"""

class PdgApiError(Exception):
    """PDG API base exception."""
    pass

class PdgInvalidPdgId(Exception):
    """Exception raised when encountering an invalid PDG Identifier."""
    pass

class PdgNoDataError(Exception):
    """Exception raised if no data is found."""
    pass

class PdgAmbiguousValue(Exception):
    """Exception raised in cases where the choice of value is ambiguous and there is no single best value."""
    pass
