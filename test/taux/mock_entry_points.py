"""
A class & function to mock the plugin mechanics
"""

from unittest.mock import Mock

from pii_extract.build.collector.defs import PII_EXTRACT_PLUGIN_ID

from taux.task_examples import TASK_PHONE_NUMBER, TASK_GOVID, TASK_CREDIT_CARD


# ---------------------------------------------------------------------


class PluginMock:

    version = "0.999"
    description = "A plugin mock description"

    def __init__(self, debug=None):
        pass

    def get_tasks(self):
        return iter([TASK_PHONE_NUMBER, TASK_GOVID, TASK_CREDIT_CARD])



def mock_entry_points(monkeypatch, module):
    """
    Monkey-patch the entry_points call to return a fake plugin class
    """
    mock_entry = Mock()
    mock_entry.name = "piisa-detectors-mock"
    mock_entry.load = Mock(return_value=PluginMock)

    mock_ep = Mock(return_value={PII_EXTRACT_PLUGIN_ID: [mock_entry]})

    monkeypatch.setattr(module, 'entry_points', mock_ep)
