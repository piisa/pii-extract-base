"""
A task collector that searches for Python entry points that correspond to
pii-extract plugins

A plugin must have 
  * an entry point of group PII_EXTRACT_PLUGIN_ID
  * the entry point must be a class with:
     - a constructor with an optional "debug" keyword argument
     - a `get_tasks()` method delivering an iterable of task definitions, with
       an optional "lang" argument to restrict to a specific language
     - optional attributes `source`, `version` and `description`
"""

from importlib.metadata import entry_points

from typing import Dict, List, Iterable

from pii_data.helper.exception import ProcException

from .base import BaseTaskCollector
from .defs import PII_EXTRACT_PLUGIN_ID

# --------------------------------------------------------------------------


class PluginTaskCollector(BaseTaskCollector):

    def __init__(self, debug: bool = False):
        """
        Check available plugins and create an instance
        """
        super().__init__(debug=debug)
        self._tasks = None
        self._plugins = []

        for entry in entry_points().get(PII_EXTRACT_PLUGIN_ID, []):

            LoaderClass = entry.load()
            self._dbgout(". LOAD PLUGIN: {}", entry.name)        
            try:
                plugin = LoaderClass(debug=debug)
            except Exception as e:
                raise ProcException("cannot instantiate plugin '{}': {}",
                                    entry.name, e)
            desc = {
                'name': entry.name,
                'source': getattr(plugin, "source", entry.name),
                'version': getattr(plugin, "version", None),
                'description': getattr(plugin, "description", None),
                'object': plugin
            }
            self._plugins.append(desc)


    def __repr__(self) -> str:
        return f'<PluginTaskCollector: #{len(self._plugins)}>'


    def list_plugins(self) -> List[Dict]:
        """
        Return the list of loaded plugins
        """
        return self._plugins


    def _gather_tasks(self) -> Iterable[Dict]:
        """
        Return all tasks
        """
        # Build the list of tasks, if we don't have it yet
        if self._tasks is None:
            self._tasks = []
            for plugin in self._plugins:
                self._tasks += list(plugin["object"].get_tasks())
        # Return it
        return iter(self._tasks)
