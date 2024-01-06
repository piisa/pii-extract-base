"""
A task collector that searches for Python entry points that correspond to
pii-extract plugins, providing lists of PiiTask descriptors

A plugin must have
  * an entry point of group PII_EXTRACT_PLUGIN_ID
  * the entry point must be a class with:
     - a constructor with a `config` argument, an optional "debug" keyword
       argument, and possibly additional arguments
     - a `get_plugin_tasks()` method delivering an iterable of *raw* task
       descriptors, with an optional "lang" argument to restrict to a specific
       language
     - optional class attributes `source`, `version` and `description`
"""

from sys import version_info
from importlib.metadata import entry_points

from typing import Dict, List, Iterable

from pii_data.helper.exception import ProcException

from pii_extract.defs import FMT_CONFIG_PLUGIN
from pii_extract.helper.types import TYPE_STR_LIST
from .utils import RawTaskDefaults
from .base import BaseTaskCollector
from .defs import PII_EXTRACT_PLUGIN_ID


# --------------------------------------------------------------------------


class PluginTaskCollector(BaseTaskCollector):

    def __init__(self, config: Dict = None, debug: bool = False,
                 languages: Iterable[str] = None):
        """
        Check available plugins and create an instance
         :param config: a dictionary possibly containing:
            (a) configuration for the collector (options for plugin loaders)
            (b) configuration to pass to each loader class
        """
        super().__init__(languages=languages, debug=debug)
        self._tasks = None
        self._plugins = []

        # Fetch all available plugins
        if version_info.minor < 10:
            plugin_list = entry_points().get(PII_EXTRACT_PLUGIN_ID, [])
        else:
            plugin_list = entry_points().select(group=PII_EXTRACT_PLUGIN_ID)

        # Get configuration for plugins
        plugin_cfg = config.get(FMT_CONFIG_PLUGIN, {}) if config else {}

        # See if we have a defined load order
        order = plugin_cfg.get("plugin-order")
        if order:
            def sortkey(v):
                try:
                    p = order.index(v.name)
                    return f"{p:03d}"
                except ValueError:
                    return v.name

            plugin_list = sorted(plugin_list, key=sortkey)

        # Get custom cfg for plugins (for backwards compat, use also the base cfg)
        custom_cfg = plugin_cfg.get("plugins") or plugin_cfg

        # Instantiate all plugins
        for entry in plugin_list:

            # See if we have custom options to instantiate this plugin
            cfg = custom_cfg.get(entry.name, {})
            if not cfg.get("load", True):
                continue        # plugin is not to be activated
            options = cfg.get("options", {})
            if self._lang:
                options["languages"] = self._lang

            # Get the class for the plugin loader
            LoaderClass = entry.load()
            self._log(". load plugin: %s", entry.name)

            # Instantiate it
            try:
                plugin = LoaderClass(config=config, **options, debug=debug)
            except Exception as e:
                raise ProcException("cannot instantiate plugin '{}': {}",
                                    entry.name, e) from e

            # Create the plugin descriptor
            desc = {
                'name': entry.name,
                'source': getattr(plugin, "source", entry.name),
                'version': getattr(plugin, "version", None),
                'description': getattr(plugin, "description", None),
                'object': plugin
            }

            # Add to the list of loaded plugins
            self._plugins.append(desc)
            self._log(". loaded plugin: %s version=%s source=%s",
                      desc["name"], desc["version"], desc["source"])


    def __repr__(self) -> str:
        return f'<PluginTaskCollector: #{len(self._plugins)}>'


    def list_plugins(self) -> List[Dict]:
        """
        Return the list of loaded plugins
        """
        return self._plugins


    def _gather_tasks(self, lang: TYPE_STR_LIST = None) -> Iterable[Dict]:
        """
        Return all tasks
        """
        if lang is None and self._tasks:
            return iter(self._tasks)

        # Build the list of tasks
        tasks = []
        reformat = RawTaskDefaults(normalize=True)
        for plugin in self._plugins:
            self._log(". gather plugin tasks for: %s", plugin["name"])
            raw_tasks = plugin["object"].get_plugin_tasks(lang)
            tasks += list(reformat(raw_tasks))

        # Store it for repeated calls
        if lang is None:
            self._tasks = tasks

        return iter(tasks)
