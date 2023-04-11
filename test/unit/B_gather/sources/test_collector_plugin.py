"""
Test the PluginTaskCollector class
"""

import pytest

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY

import pii_extract.gather.collection.sources.plugin as mod

from taux import auxpatch

@pytest.fixture
def fixture_entry_points(monkeypatch):
    auxpatch.patch_entry_points(monkeypatch)


# ---------------------------------------------------------------------


def test100_constructor(fixture_entry_points):
    """
    Check the constructor
    """
    tc = mod.PluginTaskCollector()
    assert str(tc) == '<PluginTaskCollector: #1>'


def test110_list(fixture_entry_points):
    """
    Check listing plugins
    """
    tc = mod.PluginTaskCollector()
    pl = tc.list_plugins()

    assert isinstance(pl, list)
    assert len(pl) == 1
    assert isinstance(pl[0], dict)
    assert pl[0]['name'] == 'piisa-detectors-mock-plugin'
    assert pl[0]['version'] == '0.999'
    assert isinstance(pl[0]['object'], auxpatch.PluginMock)


def test120_language_list(fixture_entry_points):
    """
    Check the list of languages
    """
    tc = mod.PluginTaskCollector()
    got = tc.language_list()
    assert [LANG_ANY, "en"] == list(got)


def test130_gather_all_tasks(fixture_entry_points):
    """
    Get all tasks
    """
    tc = mod.PluginTaskCollector()
    tasks = tc.gather_tasks()
    got = [t["pii"][0]["type"] for t in tasks]
    exp = [PiiEnum.PHONE_NUMBER, PiiEnum.GOV_ID, "CREDIT_CARD"]
    assert exp == got


def test140_gather_all_lang(fixture_entry_points):
    """
    """
    tc = mod.PluginTaskCollector()

    fetch = lambda *args: list(tc.gather_tasks(*args))

    got = fetch(LANG_ANY)
    assert len(got) == 1
    assert got[0]["pii"][0]["type"] == "CREDIT_CARD"

    got = fetch("en")
    assert len(got) == 2
    assert got[0]["pii"][0]["type"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"][0]["type"] == PiiEnum.GOV_ID

    got = fetch(["en", LANG_ANY])
    assert len(got) == 3
    assert got[0]["pii"][0]["type"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"][0]["type"] == PiiEnum.GOV_ID
    assert got[2]["pii"][0]["type"] == "CREDIT_CARD"

    got = fetch(["en", LANG_ANY, "es"])
    assert len(got) == 3

    got = fetch(["es"])
    assert len(got) == 0
