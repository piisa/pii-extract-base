"""
Test the process_file function
"""

import tempfile
from pathlib import Path
import json

from unittest.mock import Mock
import pytest

from pii_data.helper.exception import InvArgException

import pii_extract.api.file as mod



@pytest.fixture
def patch_datetime(monkeypatch):

    dt = Mock()
    dt.replace = Mock(return_value="2045-01-30")

    mock_dt_mod = Mock()
    mock_dt_mod.utcnow = Mock(return_value=dt)

    import pii_data.types.piicollection as pcmod
    monkeypatch.setattr(pcmod, 'datetime', mock_dt_mod)


# -------------------------------------------------------------------------

def test100_process_file():
    """
    Test base constructor
    """

    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        got = mod.process_file(localdoc, f1.name, lang="en", taskfile=taskfile)

    exp = {'calls': 1, 'PHONE_NUMBER': 1, 'entities': 2, 'CREDIT_CARD': 1}
    assert exp == got


def test110_process_file_result(patch_datetime):
    """
    Test base constructor
    """

    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        r = mod.process_file(localdoc, f1.name, lang="en", taskfile=taskfile)

        with open(f1.name, encoding="utf-8") as f2:
            got = json.load(f2)

    collection = Path(__file__).parents[2] / "data" / "collection-example.json"
    with open(collection, encoding="utf-8") as f:
        exp = json.load(f)

    assert exp == got


def test200_err():
    """
    Test error generation
    """
    localdoc = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"
    taskfile = Path(__file__).parents[2] / "data" / "task-spec.json"

    with tempfile.NamedTemporaryFile(suffix=".yml") as f:
        f.close()
        with pytest.raises(InvArgException):
            mod.process_file(localdoc, f.name, taskfile=taskfile)
