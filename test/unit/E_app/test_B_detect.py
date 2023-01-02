"""
Test the command-line application
"""

import tempfile
from pathlib import Path
import json

from unittest.mock import Mock
import pytest

import pii_extract.app.detect as mod

from taux import auxpatch


CONFIGFILE = Path(__file__).parents[2] / "data" / "tasklist-example.json"
DOCUMENT = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"


@pytest.fixture
def fixture_timestamp(monkeypatch):
    auxpatch.patch_timestamp(monkeypatch)

# -------------------------------------------------------------------------

def test100_detect_app(fixture_timestamp):
    """
    Test base constructor
    """
    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        args = ["--configfile", str(CONFIGFILE),
                "--lang", "en", "--skip-plugins",
                str(DOCUMENT), f1.name]
        mod.main(args)

        with open(f1.name, encoding="utf-8") as f2:
            got = json.load(f2)

    collection = Path(__file__).parents[2] / "data" / "collection-example.json"
    with open(collection, encoding="utf-8") as f:
        exp = json.load(f)

    assert exp == got
