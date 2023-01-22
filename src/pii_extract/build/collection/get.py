"""
Gather and return the collection of tasks from all available sources
"""

from typing import Dict

from ...defs import FMT_CONFIG_TASKS
from ...gather.collector import PluginTaskCollector, JsonTaskCollector
from .task_collection import PiiTaskCollection


def get_task_collection(config: Dict = None, load_plugins: bool = True,
                        debug: bool = False) -> PiiTaskCollection:
    """
    Create a task collection object & collect all available tasks
     :param config: a configuration object
     :param load_plugins: load tasks from available plugins
     :param debug:
    """
    piic = PiiTaskCollection()

    # Add task descriptors from installed plugins
    if load_plugins:
        c = PluginTaskCollector(config=config, debug=debug)
        piic.add_collector(c)

    # Add task descriptors from JSON configs
    task_cfg = config.get(FMT_CONFIG_TASKS) if config else None
    if task_cfg:
        c = JsonTaskCollector(debug=debug)
        c.add_tasks(task_cfg)
        piic.add_collector(c)

    return piic
