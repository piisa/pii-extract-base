"""
Detection and (mocked) validation of Australian Tax File Number (TFN).

"""
import re

from typing import Iterable

from pii_data.types import PiiEnum


_TFN_PATTERN = r"\b (?: \d{3} \s \d{3} \s \d{3} | \d{8,9} ) \b"
_TFN_REGEX = re.compile(_TFN_PATTERN, flags=re.X)


def _valid_tfn(tfn: str) -> bool:
    """
    a mock for a TFN validator
    """
    return True


def tax_file_number_example(doc: str) -> Iterable[str]:
    """
    Australian Tax File Number (detect and validate)
    """
    for candidate in _TFN_REGEX.findall(doc):
        if _valid_tfn(candidate):
            yield candidate


PII_TASKS = [(PiiEnum.GOV_ID, tax_file_number_example)]
