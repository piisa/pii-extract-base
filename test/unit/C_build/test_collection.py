"""
Test the build_task callable & the PiiTaskCollection class
"""

from typing import Dict

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY, COUNTRY_ANY
from pii_extract.build.task import BasePiiTask, CallablePiiTask, RegexPiiTask

import pii_extract.build.collection.task_collection as mod

from taux.task_collector_example import MyTestTaskCollector
import taux.examples_task_descriptor_full as TASKD


def _add_defaults(task: Dict) -> Dict:
    out = task.copy()
    out["info"].update({'source': 'piisa:pii-extract-base:test',
                        'version': '0.0.1'})
    return out


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
    Search a PII task, various languages
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    for lang in (LANG_ANY, "en", "pt"):
        got = list(tc.taskdef_list(lang=lang, pii=PiiEnum.CREDIT_CARD))
        assert len(got) == 1
        assert _add_defaults(TASKD.TASK_CREDIT_CARD) == got[0]

    # Now we don't allow "any language" tasks
    got = list(tc.taskdef_list("en", pii=PiiEnum.CREDIT_CARD, add_any=False))
    assert len(got) == 0


def test221_task_search():
    """
    Search a PII task, specific country
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    for c in ("au", None):
        got = list(tc.taskdef_list(lang="en", country=c, pii=PiiEnum.GOV_ID))
        assert len(got) == 1
        assert _add_defaults(TASKD.TASK_GOVID) == got[0]


def test222_task_search():
    """
    Search task, specific country
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    exp = _add_defaults(TASKD.TASK_PHONE_NUMBER)
    for c in ("au", "us", COUNTRY_ANY, None):
        got = list(tc.taskdef_list("en", c, pii=PiiEnum.PHONE_NUMBER))
        assert len(got) == 1
        assert exp == got[0]


def test223_task_search():
    """
    Search task, no matches
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    got = list(tc.taskdef_list("en", "gb", pii=PiiEnum.GOV_ID))
    assert len(got) == 0

    got = list(tc.taskdef_list(country="pt", pii=PiiEnum.GOV_ID))
    assert len(got) == 0

    got = list(tc.taskdef_list("en", pii=PiiEnum.PERSON))
    assert len(got) == 0


def test224_task_search():
    """
    Search task, no matches
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    got = list(tc.taskdef_list("en", "us", PiiEnum.PHONE_NUMBER, add_any=False))
    assert len(got) == 0

    got = list(tc.taskdef_list("pt", pii=PiiEnum.PHONE_NUMBER))
    assert len(got) == 0


def test230_task_all():
    """
    Get all tasks
    """
    tc = mod.PiiTaskCollection()
    tcol = MyTestTaskCollector()
    tc.add_collector(tcol)

    got = list(tc.taskdef_list())
    assert len(got) == 3

    pii_list = [t["piid"]["pii"] for t in got]
    assert pii_list == [PiiEnum.CREDIT_CARD, PiiEnum.PHONE_NUMBER,
                        PiiEnum.GOV_ID]

    assert got[0] == _add_defaults(TASKD.TASK_CREDIT_CARD)
    assert got[1] == _add_defaults(TASKD.TASK_PHONE_NUMBER)
    assert got[2] == _add_defaults(TASKD.TASK_GOVID)


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

    # Build a single task
    for t in ("CREDIT_CARD", ["CREDIT_CARD"], PiiEnum.CREDIT_CARD):
        got = build(pii=t)
        assert len(got) == 1
        assert got[0].pii_info.pii == PiiEnum.CREDIT_CARD

    # Build a list of tasks
    tlist = ["GOV_ID", PiiEnum.CREDIT_CARD]
    got = build(pii=tlist)
    assert len(got) == 2
    assert got[0].pii_info.pii == PiiEnum.CREDIT_CARD
    assert got[1].pii_info.pii == PiiEnum.GOV_ID
