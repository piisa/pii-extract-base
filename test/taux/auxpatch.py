"""
Several functions that can be used to patch module objects, so as to enable
normalized tests.
They all use the "monkeypatch" pytest fixture
"""

from typing import Dict, Iterable

from unittest.mock import Mock

from pii_data.types.piicollection import collection
from pii_data.types.doc import document

from pii_extract.gather.collection.sources.defs import PII_EXTRACT_PLUGIN_ID
import pii_extract.gather.collection.sources.plugin as plugin_mod

import taux.examples_task_descriptor_raw as RAW


def patch_timestamp(monkeypatch):
    """
    Monkey-patch the piicollection module to ensure the timestamps it produces
    have always the same value
    """
    dt = Mock()
    dt.replace = Mock(return_value="2045-01-30")

    mock_dt_mod = Mock()
    mock_dt_mod.utcnow = Mock(return_value=dt)

    monkeypatch.setattr(collection, 'datetime', mock_dt_mod)


def patch_uuid(monkeypatch):
    """
    Monkey-patch the document module to ensure a fixed uuid
    """
    mock_uuid = Mock()
    mock_uuid.uuid4 = Mock(return_value="00000-11111")
    monkeypatch.setattr(document, 'uuid', mock_uuid)


# ------------------------------------------------------------------------

class PluginMock:

    version = "0.999"
    description = "A plugin mock description"

    def __init__(self, config: Dict = None, debug: bool = None,
                 languages: Iterable[str] = None):
        self.languages = set(languages) if languages else None

    def get_plugin_tasks(self, lang: str = None):
        data = [RAW.TASK_PHONE_NUMBER, RAW.TASK_GOVID, RAW.TASK_CREDIT_CARD]
        if self.languages:
            print("\nDATA", data)
            f = lambda d: (d.get("lang") or d["pii"][0]["lang"]) in self.languages
            data = filter(f, data)
        return iter(data)


def patch_entry_points(monkeypatch):
    """
    Monkey-patch the the importlib.metadata.entry_points call to return
    our plugin entry point
    """
    mock_entry = Mock()
    mock_entry.name = "piisa-detectors-mock-plugin"
    mock_entry.load = Mock(return_value=PluginMock)

    mock_ep = Mock(return_value={PII_EXTRACT_PLUGIN_ID: [mock_entry]})

    monkeypatch.setattr(plugin_mod, 'entry_points', mock_ep)
