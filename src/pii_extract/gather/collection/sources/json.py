"""
Build lists of PiiTask descriptors by reading a JSON definition
"""

from typing import Dict, Iterable, Union

from pii_data.helper.exception import InvArgException, ConfigException
from pii_data.helper.config import load_config, TYPE_CONFIG
from pii_data.defs import FMT_CONFIG_PREFIX

from pii_extract.defs import FMT_CONFIG_TASKS
from pii_extract.helper.types import TYPE_STR_LIST
from pii_extract.helper.utils import taskd_field, field_set
from .utils import RawTaskDefaults
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
        if not task_spec:
            raise ConfigException("invalid task config: no task spec")

        fmt = task_spec.get("format")
        if fmt != FMT_CONFIG_PREFIX + FMT_CONFIG_TASKS:
            raise ConfigException("invalid format field '{}' in task spec", fmt)

        header = task_spec.get("header", {})
        reformat = RawTaskDefaults(header, normalize=True, languages=self._lang)
        rawlist = task_spec.get("tasklist", [])
        try:
            yield from reformat(rawlist)
        except Exception as e:
            raise InvArgException("error in task spec: {}", e) from e


    def add_tasks(self, tasks: Union[Dict, TYPE_CONFIG]):
        """
        Add to the object a list of tasks
          :param tasks: task definitions to add. It can be:
            - a dictionary of task definitions
            - a filename for a config file (JSON or YAML) with task definitions
            - a list of such filenames
        """
        if not isinstance(tasks, Dict):
            self._log(".. read taskfile: %s", tasks)
            cfg = load_config(tasks, formats=FMT_CONFIG_TASKS)
            try:
                tasks = cfg[FMT_CONFIG_TASKS]
            except KeyError:
                raise ConfigException("no task config in '{}'", tasks)

        self.tasks += list(self._parse_tasks(tasks))


    def _gather_tasks(self, lang: TYPE_STR_LIST = None) -> Iterable[Dict]:
        """
        Return an iterator over tasks
        """
        if not lang:
            yield from iter(self.tasks)
            return

        langset = field_set(lang)
        for t in self.tasks:
            if taskd_field(t["pii"], "lang") & langset:
                yield t
