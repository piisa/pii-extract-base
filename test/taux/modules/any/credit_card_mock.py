"""
Test example for credit cards
"""

import re

from typing import Iterable

from pii_data.types import PiiEnum, PiiEntityInfo, PiiEntity
from pii_data.types.doc import DocumentChunk
from pii_extract.build.task import BasePiiTask
from pii_extract.defs import LANG_ANY

# ----------------------------------------------------------------------------

# base regex to detect candidates to credit card numbers
_CREDIT_PATTERN_BASE = r"\b \d (?:\d[ -]?){14} \d \b"

# full regex for credit card type
# https://www.regular-expressions.info/creditcard.html
_CREDIT_PATTERN = r"""4[0-9]{12}(?:[0-9]{3})? |
                      (?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12} |
                      3[47][0-9]{13} |
                      3(?:0[0-5]|[68][0-9])[0-9]{11} |
                      6(?:011|5[0-9]{2})[0-9]{12} |
                      (?:2131|1800|35\d{3})\d{11}"""

# compiled regexes
_REGEX_CC_BASE = None
_REGEX_CC_FULL = None


class CreditCardMock(BasePiiTask):
    """
    A simple credit card number detection for most international credit cards
    """

    pii_name = "standard credit card"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Compile the credit card regexes
        global _REGEX_CC_FULL, _REGEX_CC_BASE
        if _REGEX_CC_FULL is None:
            _REGEX_CC_BASE = re.compile(_CREDIT_PATTERN_BASE, flags=re.VERBOSE)
            _REGEX_CC_FULL = re.compile(_CREDIT_PATTERN, flags=re.VERBOSE)


    def find(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        info = PiiEntityInfo(PiiEnum.CREDIT_CARD, LANG_ANY,
                             subtype=CreditCardMock.pii_name)
        # First find candidates
        for cc in _REGEX_CC_BASE.finditer(chunk.data):
            cc_value = cc.group()
            # strip spaces and dashes
            strip_cc = re.sub(r"[ -]+", "", cc_value)
            # now validate the credit card number
            if re.fullmatch(_REGEX_CC_FULL, strip_cc):
                yield PiiEntity(info, cc_value, chunk.id, cc.start())


# ---------------------------------------------------------------------

PII_TASKS = [(PiiEnum.CREDIT_CARD, CreditCardMock)]
