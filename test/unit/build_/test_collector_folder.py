"""
Test the FolderTaskCollector class
"""

from typing import Dict, Iterable

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY
from pii_extract.build.task import BasePiiTask

from taux.task_collector_example import MyTestTaskCollector


# ---------------------------------------------------------------------

def check_task_cc(task: Dict):
    assert len(task) == 9
    assert sorted(task.keys()) == [
        "country",
        "doc",
        "lang",
        "name",
        "pii",
        "source",
        "task",
        "type",
        "version"
    ]

    assert task["lang"] == "any"
    assert task["country"] == "any"
    assert task["pii"] == PiiEnum.CREDIT_CARD
    assert issubclass(task["task"], BasePiiTask)
    assert task["type"] == "PiiTask"
    assert task["name"] == "standard credit card"
    assert task["doc"] == "Credit card numbers for most international credit cards (detect & validate)"
    assert task["source"] == "piisa:pii-extract-base:test"
    assert task["version"] == "0.0.1"


def check_tasklist(tasklist: Iterable[Dict]):

    tasklist = list(tasklist)
    assert len(tasklist) == 3
    exp = [PiiEnum.CREDIT_CARD, PiiEnum.PHONE_NUMBER, PiiEnum.GOV_ID]
    got = [t["pii"] for t in tasklist]
    assert exp == got

    # Check the first element
    check_task_cc(tasklist[0])


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

    got = list(tc.gather_tasks(LANG_ANY))
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.CREDIT_CARD

    got = list(tc.gather_tasks("en"))
    assert len(got) == 2
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"] == PiiEnum.GOV_ID

    got = list(tc.gather_tasks("en", "any"))
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER

    got = list(tc.gather_tasks("en", "au"))
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.GOV_ID


def test130_gather_all():
    """
    """
    tc = MyTestTaskCollector()
    tasklist = tc.gather_all_tasks()
    check_tasklist(tasklist)


def test140_gather_all_lang():
    """
    """
    tc = MyTestTaskCollector()
    tasklist = tc.gather_all_tasks([LANG_ANY, "en"])
    check_tasklist(tasklist)


def test150_gather_all_lang():
    """
    """
    tc = MyTestTaskCollector()

    tasklist = list(tc.gather_all_tasks("en"))
    assert len(tasklist) == 2
    exp = [PiiEnum.PHONE_NUMBER, PiiEnum.GOV_ID]
    got = [t["pii"] for t in tasklist]
    assert exp == got

    tasklist = list(tc.gather_all_tasks(LANG_ANY))
    assert len(tasklist) == 1
    check_task_cc(tasklist[0])
