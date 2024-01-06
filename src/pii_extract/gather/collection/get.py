"""
Gather and return the collection of tasks from all available sources
"""

from typing import Dict, Iterable, Union

from pii_data.helper.logger import PiiLogger

from ...defs import FMT_CONFIG_TASKS, FMT_CONFIG_TASKCFG
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
    LOGGER("TaskCol: get_task_collection")

    task_cfg = config.get(FMT_CONFIG_TASKCFG) if config else None
    piic = PiiTaskCollection(task_config=task_cfg, debug=debug)
    if languages:
        languages = [languages] if isinstance(languages, str) else list(languages)

    # Add task descriptors from installed plugins
    if load_plugins:
        LOGGER("TaskCol: load plugin tasks")
        c = PluginTaskCollector(config=config, languages=languages, debug=debug)
        piic.add_collector(c)

    # Add the additional custom task descriptors defined in config
    add_task_cfg = config.get(FMT_CONFIG_TASKS) if config else None
    if add_task_cfg:
        src = add_task_cfg.get("header", {}).get("source", "<CONFIG>")
        LOGGER("TaskCol: load JSON tasks from: %s", src)
        c = JsonTaskCollector(languages=languages, debug=debug)
        c.add_tasks(add_task_cfg)
        piic.add_collector(c)

    return piic
