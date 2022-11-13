"""
Test the PluginTaskCollector class
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY

import pii_extract.build.collector.plugin as mod

from taux.task_examples import TASK_PHONE_NUMBER, TASK_GOVID, TASK_CREDIT_CARD
from taux.mock_entry_points import mock_entry_points, PluginMock

@pytest.fixture
def patch_entry_point(monkeypatch):
    mock_entry_points(monkeypatch, mod)

# ---------------------------------------------------------------------


def test100_constructor(patch_entry_point):
    """
    Check the constructor
    """
    tc = mod.PluginTaskCollector()
    assert str(tc) == '<PluginTaskCollector: #1>'


def test110_list(patch_entry_point):
    """
    Check the constructor
    """
    tc = mod.PluginTaskCollector()
    pl = tc.list_plugins()
    assert isinstance(pl, list)
    assert len(pl) == 1
    assert isinstance(pl[0], dict)
    assert pl[0]['name'] == 'piisa-detectors-mock'
    assert pl[0]['version'] == '0.999'
    assert isinstance(pl[0]['object'], PluginMock)


def test120_language_list(patch_entry_point):
    """
    Check the list of languages
    """
    tc = mod.PluginTaskCollector()
    got = tc.language_list()
    assert [LANG_ANY, "en"] == list(got)


def test130_gather_all_tasks(patch_entry_point):
    """
    Get all tasks
    """
    tc = mod.PluginTaskCollector()
    got = tc.gather_all_tasks()
    assert [TASK_CREDIT_CARD, TASK_PHONE_NUMBER, TASK_GOVID] == list(got)


def test140_gather_all_lang(patch_entry_point):
    """
    """
    tc = mod.PluginTaskCollector()

    fetch = lambda *args: list(tc.gather_all_tasks(*args))

    got = fetch(LANG_ANY)
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.CREDIT_CARD

    got = fetch("en")
    assert len(got) == 2
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"] == PiiEnum.GOV_ID

    got = fetch(["en", LANG_ANY])
    assert len(got) == 3
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"] == PiiEnum.GOV_ID
    assert got[2]["pii"] == PiiEnum.CREDIT_CARD

    got = fetch(["en", LANG_ANY, "es"])
    assert len(got) == 3

    got = fetch(["es"])
    assert len(got) == 0
