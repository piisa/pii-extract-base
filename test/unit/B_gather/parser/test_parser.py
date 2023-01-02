"""
Test the base task processing options in taskdict
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import COUNTRY_ANY

import pii_extract.gather.parser.parser as mod


# to be imported as regex-external
_REGEX = r"\d33"


def test10_task():
    """
    Check the function parsing a PII_TASKS list, single entry
    """
    tdesc = {
        "pii": [{"type": PiiEnum.CREDIT_CARD, "subtype": "toy regex"}],
        "class": "regex",
        "task": r"\d16",
        "doc": "this is a toy Credit Card example"
    }

    defaults = {"lang": "en", "country": "any", "source": "piisa:unit-test"}
    got = mod.parse_task_descriptor(tdesc, defaults)
    assert isinstance(got, dict)

    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD:toy regex",
            "doc": "this is a toy Credit Card example",
            "source": "piisa:unit-test"
        },
        "piid": {
            "pii": PiiEnum.CREDIT_CARD,
            "subtype": "toy regex",
            "lang": "en",
            "country": "any",
            "method": "regex"
        }
    }
    assert exp == got


def test20_defaults_lang_country():
    """
    Check the function parsing a PII_TASK, w/ language & country
    """

    def callable_example(x):
        """
        A dummy callable 
        """
        return x

    defaults = {"lang": "en", "country": ["in", "gb"]}

    tdesc = {
        "class": "regex",
        "task": r"\d16",
        "pii": [{"type": PiiEnum.CREDIT_CARD}]
    }
    got = mod.parse_task_descriptor(tdesc, defaults)
    exp = {
        "piid": [
            {
                "pii": PiiEnum.CREDIT_CARD,
                "lang": "en",
                "country": "in",
                "method": "regex"
            },
            {
                "pii": PiiEnum.CREDIT_CARD,
                "lang": "en",
                "country": "gb",
                "method": "regex"
            }
        ],
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD",
        }
    }
    assert exp == got

    tdesc = {
        "class": "callable",
        "task": callable_example,
        "pii": [{"type": PiiEnum.BLOCKCHAIN_ADDRESS, "subtype": "bitcoin"}]
    }
    got = mod.parse_task_descriptor(tdesc, defaults)
    exp = {
        "piid": [
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "subtype": "bitcoin",
                "lang": "en",
                "country": "in"
            },
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "subtype": "bitcoin",
                "lang": "en",
                "country": "gb"
            }
        ],
        "obj": {
            "class": "callable",
            "task": callable_example
        },
        "info": {
            "name": "callable example",
            "doc": "A dummy callable"
        }
    }
    assert exp == got


def test30_multiple_pii():
    """
    Check task descriptor parsing, w/ a multiple pii entry
    """

    tdesc = {
        "pii": [{"type": PiiEnum.CREDIT_CARD},
                {"type": PiiEnum.BLOCKCHAIN_ADDRESS}],
        "class": "regex",
        "task": r"\d16",
        "description": "a toy example"
    }
    defaults = {
        "lang": "en",
        "country": COUNTRY_ANY,
        "source": "unit-tests"
    }
    got = mod.parse_task_descriptor(tdesc, defaults)
    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "source": "unit-tests",
            "name": "regex for BLOCKCHAIN_ADDRESS/CREDIT_CARD"
        },
        "piid": [
            {
                "pii": PiiEnum.CREDIT_CARD,
                "lang": "en",
                "country": "any",
                "method": "regex"
            },
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "lang": "en",
                "country": "any",
                "method": "regex"
            }
        ]
    }
    assert exp == got


def test31_multiple_pii_subtype():
    """
    Check task descriptor parsing, w/ a multiple pii entry & subtypes
    """

    tdesc = {
        "pii": [{"type": PiiEnum.CREDIT_CARD, "subtype": "international"},
                {"type": PiiEnum.BLOCKCHAIN_ADDRESS, "subtype": "bitcoin"}],
        "class": "regex",
        "task": r"\d16",
        "description": "a toy example"
    }
    defaults = {
        "lang": "en",
        "country": COUNTRY_ANY,
        "source": "unit-tests"
    }
    got = mod.parse_task_descriptor(tdesc, defaults)
    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "source": "unit-tests",
            "name": "regex for BLOCKCHAIN_ADDRESS:bitcoin/CREDIT_CARD:international"
        },
        "piid": [
            {
                "pii": PiiEnum.CREDIT_CARD,
                "subtype": "international",
                "lang": "en",
                "country": "any",
                "method": "regex"
            },
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "subtype": "bitcoin",
                "lang": "en",
                "country": "any",
                "method": "regex"
            }
        ]
    }
    assert exp == got


def test32_multiple_pii_subtype_demux():
    """
    Check task descriptor parsing, w/ a subtype demux
    """

    tdesc = {
        "pii": [{"type": PiiEnum.BLOCKCHAIN_ADDRESS,
                 "subtype": ["bitcoin", "ethereum"]}],
        "class": "regex",
        "task": r"\d16",
        "description": "a toy example"
    }
    defaults = {
        "lang": "en",
        "country": COUNTRY_ANY,
        "source": "unit-tests"
    }
    got = mod.parse_task_descriptor(tdesc, defaults)
    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "source": "unit-tests",
            "name": "regex for BLOCKCHAIN_ADDRESS:bitcoin/BLOCKCHAIN_ADDRESS:ethereum"
        },
        "piid": [
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "subtype": "bitcoin",
                "lang": "en",
                "country": "any",
                "method": "regex"
            },
            {
                "pii": PiiEnum.BLOCKCHAIN_ADDRESS,
                "subtype": "ethereum",
                "lang": "en",
                "country": "any",
                "method": "regex"
            }
        ]
    }
    assert exp == got


def test36_subdict_regex_external():
    """
    Check task descriptor parsing, w/ an external regex type
    """
    PII_TASK = {
        "pii": [{"type": PiiEnum.CREDIT_CARD}],
        "class": "regex-external",
        "task": "unit.B_gather.parser.test_parser._REGEX"
    }

    got = mod.parse_task_descriptor(PII_TASK,
                                    {"lang": "en", "country": COUNTRY_ANY})
    assert got["obj"] == {"class": "regex", "task": r"\d33"}



def test50_errors():
    """
    Check task descriptor parsing with errors
    """
    # Not a dict
    PII_TASK = []
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor is not a dict"

    # Empty dict
    PII_TASK = {}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: missing field: class"

    # missing task
    PII_TASK = {"class": "regex"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: missing field: task"

    # invalid pii field
    for v in ("a string", {"d": 1}, ["string"]):
        PII_TASK = {"pii": v, "class": "regex", "task": r"\d{16}"}
        with pytest.raises(mod.InvPiiTask) as e:
            mod.parse_task_descriptor(PII_TASK)
        assert str(e.value) == "task descriptor error: pii descriptor is not a dict"

    # invalid class field
    PII_TASK = {"pii": PiiEnum.CREDIT_CARD,
                "class": "foo", "task": r"\d{16}"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: unsupported task class: foo"

    # Invalid task descriptor for a regex
    PII_TASK = {"class": "regex", "task": lambda x: x}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: regex spec should be a string"

    # Invalid task reference for an external regex
    PII_TASK = {"class": "regex-external", "task": "no.valid.reference"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: cannot import task object 'no.valid.reference': No module named 'no'"

    # Invalid task descriptor for a callable
    PII_TASK = {"class": "callable", "task": 1}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: callable spec should be a callable"
    PII_TASK = {"class": "callable", "task": "not.a.callable"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: cannot import task object 'not.a.callable': No module named 'not'"

    # Invalid task descriptor for a class
    PII_TASK = {"class": "PiiTask", "task": lambda x: x}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: class spec should be a PiiTask object"

    # Invalid PII type
    PII_TASK = {"pii": [{"type": "not.a.pii"}],
                "class": "regex", "task": r"\d{16}"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: unrecognized PiiEnum: 'NOT.A.PII'"

    # No language
    PII_TASK = {"pii": [{"type": PiiEnum.CREDIT_CARD}],
                "class": "regex", "task": r"\d{16}"}
    with pytest.raises(mod.InvPiiTask) as e:
        mod.parse_task_descriptor(PII_TASK)
    assert str(e.value) == "task descriptor error: invalid PII info set for CREDIT_CARD: missing lang"
