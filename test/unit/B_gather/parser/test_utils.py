"""
Test the base task processing options in taskdict
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import COUNTRY_ANY

import pii_extract.gather.parser.utils as mod


_SRC = [

    (PiiEnum.CREDIT_CARD, r"\d16", "toy regex"),

    {
        "pii": {"type": PiiEnum.CREDIT_CARD, "lang": "any"},
        "class": "regex",
        "task": r"\d16",
        "source": "example"
    },

    {
        "pii": PiiEnum.CREDIT_CARD,
        "class": "regex",
        "task": r"\d16",
        "doc": "this is a toy Credit Card example"
    },
]


_DST = [
    {
        'class': 'regex',
        'task': '\\d16',
        'pii': [{'type': PiiEnum.CREDIT_CARD, 'subtype': 'toy regex'}]
    },

    {
        "pii": [{"type": PiiEnum.CREDIT_CARD, "lang": "any"}],
        "class": "regex",
        "task": r"\d16",
        "source": "example"
    },

    {
        "class": "regex",
        "task": r"\d16",
        "doc": "this is a toy Credit Card example",
        "pii": [{"type": PiiEnum.CREDIT_CARD,
                 # These are repeated fields (not actually used)
                 "pii": PiiEnum.CREDIT_CARD,
                 "class": "regex",
                 "task": r"\d16",
                 "doc": "this is a toy Credit Card example"}]
    }
]


_DST_DEF = [
    {
        'class': 'regex',
        'task': '\\d16',
        'source': 'unit-tests',
        'pii': [{'type': PiiEnum.CREDIT_CARD, 'subtype': 'toy regex',
                 'lang': 'en'}]
    },

    {
        "pii": [{"type": PiiEnum.CREDIT_CARD, "lang": "any"}],
        "class": "regex",
        "task": r"\d16",
        "source": "example"
    },

    {
        "class": "regex",
        "task": r"\d16",
        "doc": "this is a toy Credit Card example",
        "source": "unit-tests",
        "pii": [{"type": PiiEnum.CREDIT_CARD,
                 "lang": "en",
                 # These are repeated fields (not actually used)
                 "pii": PiiEnum.CREDIT_CARD,
                 "class": "regex",
                 "task": r"\d16",
                 "doc": "this is a toy Credit Card example"}]
    }
]



@pytest.mark.parametrize("src,exp", zip(_SRC, _DST))
def test10_normalize(src, exp):
    """
    Check the function parsing a PII_TASKS list, single entry
    """
    got = mod.normalize_rawtaskd(src)
    assert exp == got


@pytest.mark.parametrize("src,exp", zip(_SRC, _DST_DEF))
def test20_defaults(src, exp):
    """
    Check the function parsing a PII_TASKS list, single entry
    """
    defaults = {"source": "unit-tests", "lang": "en"}

    defaulter = mod.RawTaskDefaults(defaults)

    got = defaulter([src])
    assert exp == next(got)

