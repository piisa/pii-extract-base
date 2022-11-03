
from pii_data.helper.exception import PiiDataException, InvArgException


class PiiDetectException(PiiDataException):
    pass

class PiiUnimplemented(PiiDetectException):
    pass

class CountryNotAvailable(PiiUnimplemented):
    pass

class LangNotAvailable(PiiUnimplemented):
    pass
