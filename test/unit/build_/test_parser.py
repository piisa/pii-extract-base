"""
Test the base task processing options in taskdict
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import COUNTRY_ANY

import pii_extract.build.parser as mod


_TASK = [
    # As a tuple
    (PiiEnum.CREDIT_CARD, r"\d16", "toy regex for a Credit Card"),
    # As a dict
    {
        "pii": PiiEnum.CREDIT_CARD,
        "type": "regex",
        "task": r"\d16",
        "name": "toy regex for a Credit Card",
        "doc": "this is a toy Credit Card example"
    },
]


_REGEX = r"\d33"


def tasklist(*args, **kwargs):
    """
    Wrap the call to traverse the iterator
    """
    return list(mod.build_tasklist(*args, **kwargs))


@pytest.mark.parametrize("task", _TASK)
def test31_task(task):
    """
    Check the function parsing a PII_TASKS list, single entry
    """
    tlist = tasklist([task], defaults={"lang": "en", "country": "any"})

    assert len(tlist) == 1
    assert isinstance(tlist[0], dict)

    exp = {
        "pii": PiiEnum.CREDIT_CARD,
        "lang": "en",
        "country": "any",
        "type": "regex",
        "task": r"\d16",
        "name": "toy regex for a Credit Card"
    }
    if isinstance(task, dict):
        exp["doc"] = "this is a toy Credit Card example"

    assert exp == tlist[0]


def test32_task_multiple_same():
    """
    Check the function parsing a PII_TASKS list, multiple entries, same task
    """
    tlist = tasklist(_TASK, defaults={"lang": "es", "country": "ar"})
    assert len(tlist) == 2

    exp = {
        "pii": PiiEnum.CREDIT_CARD,
        "lang": "es",
        "country": "ar",
        "type": "regex",
        "task": r"\d16",
        "name": "toy regex for a Credit Card",
    }
    assert tlist[0] == exp
    exp["doc"] = "this is a toy Credit Card example"
    assert tlist[1] == exp


def test33_task_multiple_different():
    """
    Check the function parsing a PII_TASKS list, multiple different entries
    """

    def toy_example(x):
        """another toy example"""
        return x

    PII_TASKS = [
        (PiiEnum.CREDIT_CARD, r"\d16", "a toy Credit Card regex"),
        (PiiEnum.BITCOIN_ADDRESS, toy_example),
    ]
    tlist = tasklist(PII_TASKS, defaults={"lang": "zh", "country": "cn"})

    assert len(tlist) == 2

    exp1 = {
        "pii": PiiEnum.CREDIT_CARD,
        "lang": "zh",
        "country": "cn",
        "type": "regex",
        "task": r"\d16",
        "name": "a toy Credit Card regex"
    }
    assert tlist[0] == exp1

    exp2 = {
        "pii": PiiEnum.BITCOIN_ADDRESS,
        "lang": "zh",
        "country": "cn",
        "type": "callable",
        "task": toy_example,
        "name": "toy example",
        "doc": "another toy example",
    }

    assert tlist[1] == exp2


def test34_subdict_lang_country():
    """
    Check the function parsing a PII_TASKS list, w/ language & country
    """

    def callable_example(x):
        return x

    PII_TASKS = [
        (PiiEnum.CREDIT_CARD, r"\d16", "a toy regex for a Credit Card"),
        (PiiEnum.BITCOIN_ADDRESS, callable_example),
    ]
    tlist = tasklist(PII_TASKS, defaults={"lang": "en", "country": ["in", "gb"]})

    assert len(tlist) == 2

    exp1 = {
        "pii": PiiEnum.CREDIT_CARD,
        "lang": "en",
        "country": ["in", "gb"],
        "type": "regex",
        "task": r"\d16",
        "name": "a toy regex for a Credit Card"
    }
    assert tlist[0] == exp1

    exp2 = {
        "pii": PiiEnum.BITCOIN_ADDRESS,
        "lang": "en",
        "country": ["in", "gb"],
        "type": "callable",
        "task": callable_example,
        "name": "callable example",
    }

    assert tlist[1] == exp2


def test35_subdict_multiple_pii():
    """
    Check the function parsing a PII_TASKS list, w/ a multiple pii entry
    """

    PII_TASKS = [
        {
            "pii": [PiiEnum.CREDIT_CARD, PiiEnum.BITCOIN_ADDRESS],
            "type": "regex",
            "task": r"\d16",
            "doc": "a toy regex example",
            "lang": "any"
        }
    ]
    defaults = {
        "lang": "en",
        "country": COUNTRY_ANY,
        "source": "unit-tests"
    }
    tlist = tasklist(PII_TASKS, defaults=defaults)

    assert len(tlist) == 2

    exp1 = {
        "pii": PiiEnum.CREDIT_CARD,
        "lang": "any",
        "country": "any",
        "type": "regex",
        "task": r"\d16",
        "name": "regex for credit_card",
        "doc": "a toy regex example",
        "source": "unit-tests"
    }
    assert tlist[0] == exp1

    exp2 = {
        "pii": PiiEnum.BITCOIN_ADDRESS,
        "lang": "any",
        "country": "any",
        "type": "regex",
        "task": r"\d16",
        "name": "regex for bitcoin_address",
        "doc": "a toy regex example",
        "source": "unit-tests"
    }

    assert tlist[1] == exp2


def test36_subdict_regex_external():
    """
    Check the function parsing a PII_TASKS list, w/ an external regex type
    """
    PII_TASKS = [
        {
            "pii": PiiEnum.CREDIT_CARD,
            "type": "regex-external",
            "task": "unit.build_.test_parser._REGEX",
            "doc": "a toy regex example",
        }
    ]
    tlist = tasklist(PII_TASKS, {"lang": "en", "country": COUNTRY_ANY})
    assert len(tlist) == 1
    assert tlist[0]["task"] == r"\d33"


def test40_subdict_simplified_err():
    """
    Check the function parsing a PII_TASKS list of simplified tasks with errors
    """
    # Not a tuple
    PII_TASKS = [r"\d16"]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # A tuple plus not a tuple
    PII_TASKS = [(PiiEnum.CREDIT_CARD, r"\d{16}", "a toy Credit Card example"), r"\d16"]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "zh")

    # A tuple without a valid PiiEnum
    PII_TASKS = [("not a PiiEnum", r"\d{16}", "a toy Credit Card example")]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "es")


def test41_subdict_full_err():
    """
    Check the function parsing a PII_TASKS list of full tasks with errors
    """
    # Empty dict
    PII_TASKS = [{}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # invalid pii field
    PII_TASKS = [{"pii": "not a valid PiiEnum", "type": "regex", "task": r"\d{16}"}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # invalid type field
    PII_TASKS = [
        {"pii": PiiEnum.CREDIT_CARD, "type": "not a valid type", "task": r"\d{16}"}
    ]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # No task
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "regex"}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # Invalid task descriptor for a regex
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "regex", "task": lambda x: x}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # Invalid task reference for an external regex
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "regex-external",
                  "task": "not.a.valid.reference"}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # Invalid task descriptor for a callable
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "callable", "task": r"\d{16}"}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # Invalid task descriptor for a class
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "PiiTask", "task": lambda x: x}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS, "fr")

    # No language
    PII_TASKS = [{"pii": PiiEnum.CREDIT_CARD, "type": "regex", "task": r"\d{16}"}]
    with pytest.raises(mod.InvPiiTask):
        tasklist(PII_TASKS)
