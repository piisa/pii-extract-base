"""
Build lists of PiiTask specifications by reading a JSON definition
"""

import json
from pathlib import Path

from typing import Dict, List, Iterable, Dict

from pii_data.helper.io import openfile
from pii_data.helper.exception import InvArgException

from ...helper.types import TYPE_STR_LIST
from ..parser import build_tasklist
from .base import BaseTaskCollector


# For JSON defs: format specification string that indicates a task definition
FMT_TASK_SPEC = "piisa:piitask-spec:v1"



# --------------------------------------------------------------------------


class JsonTaskCollector(BaseTaskCollector):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks = []


    def _read_taskfile(self, filename: str) -> Iterable[Dict]:
        """
        Read a list of task descriptors from a JSON file
        """
        with openfile(filename, encoding="utf-8") as f:
            try:
                task_spec = json.load(f)
            except json.JSONDecodeError as e:
                raise InvArgException("invalid task spec file '{}': {}",
                                      filename, e) from e

            if task_spec.get("format") != FMT_TASK_SPEC:
                raise InvArgException("invalid format field in task spec '{}'",
                                      filename)
            header = task_spec.get("header", {})
            rawlist = task_spec.get("tasklist", [])
            try:
                yield from build_tasklist(rawlist, header)
            except Exception as e:
                raise InvArgException(
                    "error in task spec file '{}': {}", filename, e) from e


    def add_taskfile(self, filename: TYPE_STR_LIST):
        """
        Add to the object all tasks defined in a JSON file (or in several)
        """
        if isinstance(filename, (str, Path)):
            filename = [filename]
        for f in filename:
            self.tasks += list(self._read_taskfile(f))


    def _gather_tasks(self) -> Iterable[Dict]:
        """
        Return an iterator over tasks
        """
        return iter(self.tasks)
