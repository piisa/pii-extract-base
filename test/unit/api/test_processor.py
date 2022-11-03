"""
Test the main classes in taskdict: TaskColllector & PiiTaskCollection
"""
from pathlib import Path

from unittest.mock import Mock
import pytest

from pii_data.types import PiiEnum, PiiCollection
from pii_data.types.localdoc import LocalSrcDocumentFile
from pii_data.helper.exception import ProcException

import pii_extract.build.collector.plugin as pgmod
import pii_extract.api.processor as mod

from taux.mock_entry_points import mock_entry_points


@pytest.fixture
def patch_entry_point(monkeypatch):
    mock_entry_points(monkeypatch, pgmod)


@pytest.fixture
def patch_datetime(monkeypatch):

    dt = Mock()
    dt.replace = Mock(return_value="2045-01-30")

    mock_dt_mod = Mock()
    mock_dt_mod.utcnow = Mock(return_value=dt)

    import pii_data.types.piicollection as pcmod
    monkeypatch.setattr(pcmod, 'datetime', mock_dt_mod)


# -------------------------------------------------------------------------

def test100_constructor():
    """
    Test base constructor
    """
    pd = mod.PiiProcessor(load_plugins=False)
    assert str(pd) == '<PiiProcessor #0>'


def test110_constructor_plugin(patch_entry_point):
    """
    Test constructor, with plugins
    """
    pd = mod.PiiProcessor()
    assert str(pd) == '<PiiProcessor #3>'
    pd = mod.PiiProcessor(load_plugins=False)
    assert str(pd) == '<PiiProcessor #0>'


def test110_constructor_json():
    """
    Test constructor, with JSON
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    assert str(pd) == '<PiiProcessor #2>'

    pd = mod.PiiProcessor(load_plugins=False)
    pd.add_json_tasks(taskfile)
    assert str(pd) == '<PiiProcessor #2>'


def test120_constructor_plugin_json(patch_entry_point):
    """
    Test constructor, with plugins & JSON
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(json_tasks=taskfile)
    assert str(pd) == '<PiiProcessor #5>'
    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    assert str(pd) == '<PiiProcessor #2>'


def test130_language_list(patch_entry_point):
    """
    Test language list
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(json_tasks=taskfile)
    assert str(pd) == '<PiiProcessor #5>'
    assert list(pd.language_list()) == ["any", "en"]


def test150_task_info():
    """
    Test building a PiiTask
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    with pytest.raises(ProcException):
        pd.task_info()


def test200_build_tasks():
    """
    Test building a PiiTask
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    n = pd.build_tasks("en")
    assert n == 2
    n = pd.build_tasks("any")
    assert n == 1
    n = pd.build_tasks("en", add_any=False)
    assert n == 1


def test210_tasks_info():
    """
    Test fetching task info
    """
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"
    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")
    got = pd.task_info()
    exp = {
        (PiiEnum.CREDIT_CARD, 'any'): [
            ('standard credit card', 'Credit card numbers for most international credit cards (detect & validate)')
        ],
        (PiiEnum.PHONE_NUMBER, 'any'): [
            ('international phone number', 'detect phone numbers that use international notation. Uses context')
        ]
    }
    assert exp == got


def test220_tasks_detect(patch_datetime):
    """
    Test building a PiiTask
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(localdoc)
    r = pd.detect(doc)
    assert isinstance(r, PiiCollection)


def test230_tasks_detect_header(patch_datetime):
    """
    Test building a PiiTask
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(localdoc)
    r = pd.detect(doc)

    exp = {
        "date": "2045-01-30",
        "format": "piisa:pii-collection:v1",
        "lang": "en",
        "stage": "detection",
        "detectors": {
            1: {
                "name": "international phone number",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1"
            },
            2: {
                "name": "standard credit card",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1"
            }
        }
    }
    assert exp == r.header()


def test230_tasks_detect_pii(patch_datetime):
    """
    Test building a PiiTask
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(localdoc)
    r = pd.detect(doc)

    assert len(r) == 2
    pii = list(r)
    assert str(pii[0]) == "<PiiEntity PHONE_NUMBER:+34983453999>"
    assert str(pii[1]) == "<PiiEntity CREDIT_CARD:4273 9666 4581 5642>"


def test230_tasks_detect_pii_dict(patch_datetime):
    """
    Test building a PiiTask
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(localdoc)
    r = pd.detect(doc)

    pii = list(r)
    exp = {
        'detector': 1,
        'type': 'PHONE_NUMBER',
        'value': '+34983453999',
        'chunkid': '3',
        'country': 'any',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 44,
        'end': 56
    }
    assert exp == pii[0].as_dict()

    exp = {
        'detector': 2,
        'type': 'CREDIT_CARD',
        'value': '4273 9666 4581 5642',
        'chunkid': '4',
        'subtype': 'standard credit card',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 25,
        'end': 44
    }
    assert exp == pii[1].as_dict()


def test250_tasks_stats(patch_datetime):
    """
    Test building a PiiTask
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    pd = mod.PiiProcessor(load_plugins=False, json_tasks=taskfile)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(localdoc)
    pd.detect(doc)

    stats = pd.get_stats()
    assert stats == {'calls': 1, 'entities': 2,
                     'PHONE_NUMBER': 1, 'CREDIT_CARD': 1}
