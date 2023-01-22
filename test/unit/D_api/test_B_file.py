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

from taux import auxpatch


CONFIGFILE = Path(__file__).parents[2] / "data" / "tasklist-example.json"
DOCUMENT = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"

@pytest.fixture
def fixture_timestamp(monkeypatch):
    auxpatch.patch_timestamp(monkeypatch)


# -------------------------------------------------------------------------

def test100_process_file():
    """
    Test base constructor
    """
    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        got = mod.process_file(DOCUMENT, f1.name, lang="en", skip_plugins=True,
                               configfile=CONFIGFILE)

    exp = {'num': {'calls': 1, 'entities': 2},
           'entities': {'PHONE_NUMBER': 1, 'CREDIT_CARD': 1}}
    assert exp == got


def test110_process_file_result(fixture_timestamp):
    """
    Test base constructor
    """
    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        mod.process_file(DOCUMENT, f1.name, lang="en", skip_plugins=True,
                         configfile=CONFIGFILE)

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
    with tempfile.NamedTemporaryFile(suffix=".yml") as f:
        f.close()
        with pytest.raises(InvArgException):
            mod.process_file(DOCUMENT, f.name, configfile=CONFIGFILE)
