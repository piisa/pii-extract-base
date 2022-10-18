"""
Test the build_task callable & the PiiTaskCollection class
"""

from typing import Dict

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY, COUNTRY_ANY
from pii_extract.build.task import BasePiiTask, CallablePiiTask, RegexPiiTask

import pii_extract.load.task_collection as mod

from taux.task_examples import TASK_PHONE_NUMBER, TASK_GOVID, TASK_CREDIT_CARD
from taux.task_collector_example import MyTestTaskCollector


# -------------------------------------------------------------------------

def test100_build_regex():
    """
    Test building a PiiTask regex
    """
    task = mod.build_task(TASK_PHONE_NUMBER)
    assert isinstance(task, RegexPiiTask)


def test110_build_callable():
    """
    Test building a callable PiiTask
    """
    task = mod.build_task(TASK_GOVID)
    assert isinstance(task, CallablePiiTask)


def test120_build_task():
    """
    Test building a PiiTask
    """
    task = mod.build_task(TASK_CREDIT_CARD)
    assert isinstance(task, BasePiiTask)

# -------------------------------------------------------------------------

def add_defaults(task: Dict) -> Dict:
    return {
        **task,
        'source': 'piisa:pii-extract-base:test',
        'version': '0.0.1'
    }


def test200_constructor():
    """
    """
    tc = mod.PiiTaskCollection()
    assert str(tc) == "<PiiTaskCollection #0>"


def test210_collect():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    num = tc.add_collector(tcol)
    assert num == 3
    assert str(tc) == "<PiiTaskCollection #3>"


def test220_task_search():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    for lang in (LANG_ANY, "en", "pt"):
        got = list(tc.taskdef_list(PiiEnum.CREDIT_CARD, lang))
        assert len(got) == 1
        assert add_defaults(TASK_CREDIT_CARD) == got[0]

    got = list(tc.taskdef_list(PiiEnum.CREDIT_CARD, "en", add_any=False))
    assert len(got) == 0

    for country in ("au", None):
        got = list(tc.taskdef_list(PiiEnum.GOV_ID, "en", country))
        assert len(got) == 1
        assert add_defaults(TASK_GOVID) == got[0]

    got = list(tc.taskdef_list(PiiEnum.GOV_ID, "en", "gb"))
    assert len(got) == 0
    got = list(tc.taskdef_list(PiiEnum.GOV_ID, "pt"))
    assert len(got) == 0
    got = list(tc.taskdef_list(PiiEnum.PERSON, "en"))
    assert len(got) == 0


    for country in ("au", "us", COUNTRY_ANY, None):
        got = list(tc.taskdef_list(PiiEnum.PHONE_NUMBER, "en", country))
        assert len(got) == 1
        assert add_defaults(TASK_PHONE_NUMBER) == got[0]

    got = list(tc.taskdef_list(PiiEnum.PHONE_NUMBER, "en", "us", add_any=False))
    assert len(got) == 0
    got = list(tc.taskdef_list(PiiEnum.PHONE_NUMBER, "pt"))
    assert len(got) == 0
    

def test230_task_all():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    got = tc.taskdef_dict()
    assert len(got) == 2
    assert sorted(got) == ['any', 'en']

    exp = {
        'any': [add_defaults(TASK_CREDIT_CARD)]
    }
    assert exp == got['any']

    exp = {
        'any': [add_defaults(TASK_PHONE_NUMBER)],
        'au': [add_defaults(TASK_GOVID)]
    }

    assert exp == got['en']



def test240_task_all_lang():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    got = tc.taskdef_dict('any')
    assert len(got) == 1
    assert sorted(got) == ['any']

    exp = {
        'any': [add_defaults(TASK_CREDIT_CARD)]
    }
    assert exp == got


def test300_task_build_all():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    build = lambda *args: list(tc.build_tasks(*args))

    got = build()
    assert len(got) == 3
    exp = [BasePiiTask, RegexPiiTask, CallablePiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)


def test310_task_build_lang_country():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    build = lambda *args, **kwargs: list(tc.build_tasks(*args, **kwargs))

    # All for English
    got = build('en')
    assert len(got) == 3
    exp = [BasePiiTask, RegexPiiTask, CallablePiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)

    # All for English & Australia
    got = build('en', 'au')
    assert len(got) == 3
    exp = [BasePiiTask, RegexPiiTask, CallablePiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)

    # All for English & Australia, don't add country/lang independent tasks
    got = build('en', 'au', add_any=False)
    assert len(got) == 1
    exp = [CallablePiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)
        
    # All for English & Great Britain -- we lose GOV_ID
    got = build('en', 'gb')
    assert len(got) == 2
    exp = [BasePiiTask, RegexPiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)
        
    # All for English, don't add lang independent tasks
    # We don't add CREDIT_CARD (lang=any) but we *do* add PHONE_NUMBER
    # (country=any), since we are adding all countries
    got = build('en', add_any=False)
    assert len(got) == 2
    exp = [RegexPiiTask, CallablePiiTask]
    for e, g in zip(exp, got):
        assert isinstance(g, e)

    got = build('zh')
    assert len(got) == 1
    assert isinstance(got[0], BasePiiTask)

    got = build('zh', add_any=False)
    assert len(got) == 0


def test320_task_build_tasks():
    """
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    build = lambda *args, **kwargs: list(tc.build_tasks(*args, **kwargs))

    # Single task
    for t in ("CREDIT_CARD", ["CREDIT_CARD"], PiiEnum.CREDIT_CARD):
        got = build(tasks=t)
        assert len(got) == 1
        assert got[0].pii == PiiEnum.CREDIT_CARD

    # List of tasks
    tlist = ["GOV_ID", PiiEnum.CREDIT_CARD]
    got = build(tasks=tlist)
    assert len(got) == 2
    assert got[0].pii == PiiEnum.CREDIT_CARD
    assert got[1].pii == PiiEnum.GOV_ID
        
