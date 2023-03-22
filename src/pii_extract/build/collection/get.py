"""
Gather and return the collection of tasks from all available sources
"""

from typing import Dict

from pii_data.helper.logger import PiiLogger

from ...defs import FMT_CONFIG_TASKS
from ...gather.collector import PluginTaskCollector, JsonTaskCollector
from .task_collection import PiiTaskCollection


LOGGER = None

def get_task_collection(config: Dict = None, load_plugins: bool = True,
                        debug: bool = False) -> PiiTaskCollection:
    """
    Create a task collection object & collect all available tasks
     :param config: a configuration object
     :param load_plugins: load tasks from available plugins
     :param debug:
    """
    global LOGGER
    if LOGGER is None:
        LOGGER = PiiLogger(__name__, debug)
    LOGGER("get_task_collection")

    piic = PiiTaskCollection(debug=debug)

    # Add task descriptors from installed plugins
    if load_plugins:
        LOGGER("load plugin tasks")
        c = PluginTaskCollector(config=config, debug=debug)
        piic.add_collector(c)

    # Add task descriptors from JSON configs
    task_cfg = config.get(FMT_CONFIG_TASKS) if config else None
    if task_cfg:
        LOGGER("load JSON tasks")
        c = JsonTaskCollector(debug=debug)
        c.add_tasks(task_cfg)
        piic.add_collector(c)

    return piic
