"""
Build lists of PiiTask specifications by reading a JSON definition
"""

from typing import Dict, Iterable, Union

from pii_data.helper.exception import InvArgException, ConfigException
from pii_data.helper.config import load_config, TYPE_CONFIG

from ...defs import FMT_CONFIG_TASKS
from ..parser import build_tasklist
from .base import BaseTaskCollector


# --------------------------------------------------------------------------


class JsonTaskCollector(BaseTaskCollector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = []


    def _parse_tasks(self, task_spec: Dict) -> Iterable[Dict]:
        """
        Parse a list of task descriptors
        """
        fmt = task_spec.get("format")
        if fmt != FMT_CONFIG_TASKS:
            raise ConfigException("invalid format field '{}' in task spec", fmt)
        header = task_spec.get("header", {})
        rawlist = task_spec.get("tasklist", [])
        try:
            yield from build_tasklist(rawlist, header)
        except Exception as e:
            raise InvArgException("error in task spec: {}", e) from e


    def add_tasks(self, tasks: Union[Dict, TYPE_CONFIG]):
        """
        Add to the object a list of tasks
          :param tasks: task definitions to add. It can be:
            - a dictionary of task definitions
            - a filename for a JSON with task definitions
            - a list of filenames
        """
        if not isinstance(tasks, Dict):
            self._dbgout(".. READ TASKFILE: {}", tasks)
            cfg = load_config(tasks, formats=FMT_CONFIG_TASKS)
            tasks = cfg.get("extract_tasks")

        self.tasks += list(self._parse_tasks(tasks))


    def _gather_tasks(self) -> Iterable[Dict]:
        """
        Return an iterator over tasks
        """
        return iter(self.tasks)
