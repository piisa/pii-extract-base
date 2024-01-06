"""
Enlarge the pii-data exception hierarchy
"""

from pii_data.helper.exception import PiiDataException, InvArgException  # noqa: F401


class PiiDetectException(PiiDataException):
    pass

class PiiUnimplemented(PiiDetectException):
    pass

class CountryNotAvailable(PiiUnimplemented):
    pass

class LangNotAvailable(PiiUnimplemented):
    pass
