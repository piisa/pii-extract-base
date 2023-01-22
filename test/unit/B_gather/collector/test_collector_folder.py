"""
Test the FolderTaskCollector class
"""

from typing import Dict, Iterable

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY

from taux.task_collector_example import MyTestTaskCollector
from taux.modules.any.credit_card_mock import CreditCardMock

# ---------------------------------------------------------------------

TASK_CREDIT_CARD = {
    "class": "PiiTask",
    "task": CreditCardMock,
    "source": "piisa:pii-extract-base:test",
    "version": "0.0.1",
    "pii": [{
        "type": PiiEnum.CREDIT_CARD,
        "country": "any",
        "lang": "any"
    }]
}


def _check_tasklist(tasklist: Iterable[Dict]):

    tasklist = list(tasklist)
    assert len(tasklist) == 4
    exp = [PiiEnum.CREDIT_CARD, PiiEnum.PHONE_NUMBER,
           PiiEnum.GOV_ID, PiiEnum.GOV_ID]
    got = [t["pii"][0]["type"] for t in tasklist]
    assert exp == got

    # Check the first element
    assert tasklist[0] == TASK_CREDIT_CARD


# ---------------------------------------------------------------------


def test100_lang():
    """
    Check the list of languages
    """
    tc = MyTestTaskCollector()
    got = tc.language_list()
    assert [LANG_ANY, "en"] == got


def test110_countries():
    """
    Check the list of countries for a language
    """
    tc = MyTestTaskCollector()
    got = tc.country_list("en")
    assert [LANG_ANY, "au"] == got

    got = tc.country_list("es")
    assert [] == got


def test120_gather_tasks():
    """
    """
    tc = MyTestTaskCollector()

    # Only lang == any
    got = list(tc.gather_tasks(LANG_ANY))
    assert len(got) == 1
    assert got[0]["pii"][0] == {"type": PiiEnum.CREDIT_CARD, "country": "any",
                                "lang": "any"}

    pii_phone = {
        "type": PiiEnum.PHONE_NUMBER,
        "country": "any",
        "lang": "en",
        "context": {
            "type": "word",
            "value": ["ph", "phone", "fax"],
            "width": [16, 0]
        }
    }
    # Only lang == en (but "any" is also added)
    got = list(tc.gather_tasks("en"))
    assert len(got) == 3
    assert got[0]["pii"][0] == pii_phone
    assert got[1]["pii"][0] == {"type": PiiEnum.GOV_ID, "country": "au",
                                "subtype": "Australian Business Number",
                                "lang": "en"}

    # Only lang == en, country == any
    got = list(tc.gather_tasks("en", "any"))
    assert len(got) == 1
    assert got[0]["pii"][0] == pii_phone

    # Only lang == en, country == au
    got = list(tc.gather_tasks("en", "au"))
    assert len(got) == 2
    assert got[0]["pii"][0] == {"type": PiiEnum.GOV_ID, "country": "au",
                                "subtype": "Australian Business Number",
                                "lang": "en"}


def test130_gather_all():
    """
    """
    tc = MyTestTaskCollector()
    tasklist = tc.gather_tasks()
    _check_tasklist(tasklist)


def test140_gather_lang_single():
    """
    Test fetching tasks for a single language
    """
    tc = MyTestTaskCollector()

    tasklist = list(tc.gather_tasks("en"))
    assert len(tasklist) == 3
    exp = [PiiEnum.PHONE_NUMBER, PiiEnum.GOV_ID, PiiEnum.GOV_ID]
    got = [t["pii"][0]["type"] for t in tasklist]
    assert exp == got

    tasklist = list(tc.gather_tasks(LANG_ANY))
    assert len(tasklist) == 1
    assert tasklist[0] == TASK_CREDIT_CARD


def test150_gather_lang_any():
    """
    Test fetching tasks for language ANY
    """
    tc = MyTestTaskCollector()

    tasklist = list(tc.gather_tasks(LANG_ANY))
    assert len(tasklist) == 1
    assert tasklist[0] == TASK_CREDIT_CARD


def test160_gather_lang_list():
    """
    Test fetching tasks for a list of languages
    """
    tc = MyTestTaskCollector()
    tasklist = tc.gather_tasks([LANG_ANY, "en"])
    _check_tasklist(tasklist)


def test170_gather_all_filter():
    """
    Get all tasks, applying a PII filter
    """
    tc = MyTestTaskCollector(pii_filter=[PiiEnum.GOV_ID, PiiEnum.CREDIT_CARD])
    tasks = tc.gather_tasks()
    got = [t["pii"][0]["type"] for t in tasks]
    exp = [PiiEnum.CREDIT_CARD, PiiEnum.GOV_ID, PiiEnum.GOV_ID]
    assert exp == got
