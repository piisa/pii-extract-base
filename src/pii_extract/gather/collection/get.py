"""
Gather and return the collection of tasks from all available sources
"""

from typing import Dict, Iterable, Union

from pii_data.helper.logger import PiiLogger

from ...defs import FMT_CONFIG_TASKS
from .sources import PluginTaskCollector, JsonTaskCollector
from .task_collection import PiiTaskCollection


LOGGER = None

def get_task_collection(config: Dict = None, load_plugins: bool = True,
                        languages: Union[str, Iterable[str]] = None,
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
    if languages:
        languages = [languages] if isinstance(languages, str) else list(languages)

    # Add task descriptors from installed plugins
    if load_plugins:
        LOGGER("load plugin tasks")
        c = PluginTaskCollector(config=config, languages=languages, debug=debug)
        piic.add_collector(c)

    # Add task descriptors from JSON configs
    task_cfg = config.get(FMT_CONFIG_TASKS) if config else None
    if task_cfg:
        LOGGER("load JSON tasks")
        c = JsonTaskCollector(languages=languages, debug=debug)
        c.add_tasks(task_cfg)
        piic.add_collector(c)

    return piic
