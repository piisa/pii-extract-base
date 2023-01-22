"""
Test the base task processing options in taskdict
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import COUNTRY_ANY

import pii_extract.gather.parser.parser as mod


_TASK = [

    # As a tuple
    (PiiEnum.CREDIT_CARD, r"\d16", "toy regex"),

    # As a dict
    {
        "pii": PiiEnum.CREDIT_CARD,
        "class": "regex",
        "task": r"\d16",
        "doc": "this is a toy Credit Card example"
    },
]


_REGEX = r"\d33"


def tasklist(*args, **kwargs):
    """
    Wrap the call to traverse the iterator
    """
    return list(mod.build_task_descriptors(*args, **kwargs))


@pytest.mark.parametrize("task", _TASK)
def test31_task(task):
    """
    Check the function parsing a PII_TASKS list, single entry
    """
    tlist = tasklist([task], defaults={"lang": "en", "country": "any"})
    assert len(tlist) == 1

    got = tlist[0]
    assert isinstance(got, dict)

    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD"
        },
        "piid": {
            "pii": PiiEnum.CREDIT_CARD,
            "lang": "en",
            "country": "any",
            "method": "regex"
        }
    }
    if isinstance(task, dict):
        exp["info"]["doc"] = "this is a toy Credit Card example"
    else:
        exp["piid"]["subtype"] = "toy regex"
        exp["info"]["name"] += ":toy regex"


    assert exp == got


def test32_task_multiple_same():
    """
    Check the function parsing a PII_TASKS list, multiple entries, same task
    """
    defaults = {"lang": "es", "country": "ar", "source": "piisa:unit-test"}
    tlist = tasklist(_TASK, defaults=defaults)

    assert len(tlist) == 2

    exp = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD",
            "source": "piisa:unit-test"
        },
        "piid": {
            "pii": PiiEnum.CREDIT_CARD,
            "lang": "es",
            "country": "ar",
            "method": "regex"
        }
    }
    exp["info"]["doc"] = "this is a toy Credit Card example"
    assert tlist[1] == exp
    del exp["info"]["doc"]
    exp["piid"]["subtype"] = "toy regex"
    exp["info"]["name"] += ":toy regex"
    assert tlist[0] == exp


def test33_task_multiple_different():
    """
    Check the function parsing a PII_TASKS list, multiple different entries
    """

    def toy_example(x):
        """another toy example"""
        return x

    PII_TASKS = [
        (PiiEnum.CREDIT_CARD, r"\d16", "simple cc regex"),
        (PiiEnum.BITCOIN_ADDRESS, toy_example),
    ]
    tlist = tasklist(PII_TASKS, defaults={"lang": "zh", "country": "cn"})

    assert len(tlist) == 2

    exp1 = {
        "piid": {
            "pii": PiiEnum.CREDIT_CARD,
            "subtype": "simple cc regex",
            "lang": "zh",
            "country": "cn",
            "method": "regex"
        },
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD:simple cc regex"
        }
    }
    assert tlist[0] == exp1

    exp2 = {
        "piid": {
            "pii": PiiEnum.BITCOIN_ADDRESS,
            "lang": "zh",
            "country": "cn"
        },
        "obj": {
            "class": "callable",
            "task": toy_example
        },
        "info": {
            "name": "toy example",
            "doc": "another toy example"
        }
    }
    assert tlist[1] == exp2


def test34_subdict_lang_country():
    """
    Check the function parsing a PII_TASKS list, w/ language & country
    """

    def callable_example(x):
        return x

    PII_TASKS = [
        (PiiEnum.CREDIT_CARD, r"\d16", "toy CC"),
        (PiiEnum.BITCOIN_ADDRESS, callable_example),
    ]
    tlist = tasklist(PII_TASKS, defaults={"lang": "en", "country": ["in", "gb"]})

    assert len(tlist) == 2

    exp0 = {
        "piid": {
            "pii": PiiEnum.CREDIT_CARD,
            "subtype": "toy CC",
            "lang": "en",
            "country": ["in", "gb"],
            "method": "regex"
        },
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "name": "regex for CREDIT_CARD:toy CC"
        }
    }
    assert tlist[0] == exp0

    exp1 = {
        "piid": {
            "pii": PiiEnum.BITCOIN_ADDRESS,
            "lang": "en",
            "country": ["in", "gb"]
        },
        "obj": {
            "class": "callable",
            "task": callable_example
        },
        "info": {
            "name": "callable example"
        }
    }
    assert tlist[1] == exp1


def test35_subdict_multiple_pii():
    """
    Check the function parsing a PII_TASKS list, w/ a multiple pii entry
    """

    PII_TASKS = [
        {
            "pii": [{"type": PiiEnum.CREDIT_CARD},
                    {"type": PiiEnum.BITCOIN_ADDRESS}],
            "class": "regex",
            "task": r"\d16",
            "description": "a toy example"
        }
    ]
    defaults = {
        "lang": "en",
        "country": COUNTRY_ANY,
        "source": "unit-tests"
    }
    tlist = tasklist(PII_TASKS, defaults=defaults)

    assert len(tlist) == 1

    exp1 = {
        "obj": {
            "class": "regex",
            "task": r"\d16"
        },
        "info": {
            "source": "unit-tests",
            "name": "regex for CREDIT_CARD/BITCOIN_ADDRESS"
        },
        "piid": [
            {
                "pii": PiiEnum.CREDIT_CARD,
                "lang": "en",
                "country": "any",
                "method": "regex"
            },
            {
                "pii": PiiEnum.BITCOIN_ADDRESS,
                "lang": "en",
                "country": "any",
                "method": "regex"
            }
        ]
    }
    assert tlist[0] == exp1



def test36_subdict_regex_external():
    """
    Check the function parsing a PII_TASKS list, w/ an external regex type
    """
    PII_TASKS = [
        {
            "pii": PiiEnum.CREDIT_CARD,
            "class": "regex-external",
            "task": "unit.gather.test_parser._REGEX"
        }
    ]
    tlist = tasklist(PII_TASKS, {"lang": "en", "country": COUNTRY_ANY})
    assert len(tlist) == 1
    assert tlist[0]["obj"] == {"class": "regex", "task": r"\d33"}


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
