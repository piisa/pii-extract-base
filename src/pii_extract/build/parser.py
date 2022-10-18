"""
Build a dict of tasks from their descriptions

Each dictionary value contains a 3-4 element tuple:
 * lang
 * country
 * PiiEnum
 * task implementation
 * (for regex tasks) task documentation
"""

import importlib
import re

from typing import Dict, List, Tuple, Callable, Any, Type, Union, Iterable

from pii_data.types import PiiEnum
from pii_data.helper.exception import InvArgException

from ..defs import LANG_ANY, COUNTRY_ANY
from .task import BasePiiTask

# Name of the Python list that holds the pii tasks inside each module
_LISTNAME = "PII_TASKS"

TYPE_TASK_LIST = List[Union[Tuple, Dict]]

# --------------------------------------------------------------------------


class InvPiiTask(InvArgException):
    pass


def _is_pii_class(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, BasePiiTask)


def _import_object(objname: str) -> Union[Callable, Type[BasePiiTask]]:
    try:
        modname, oname = objname.rsplit(".", 1)
        mod = importlib.import_module(modname)
        return getattr(mod, oname)
    except Exception as e:
        raise InvPiiTask("cannot import task object '{}': {}", objname, e) from e


def _parse_taskdict(task: Dict, defaults: Dict = None) -> Dict:
    """
    Check the dict fields for a task, fill fields if needed
     :param task: the task dictionary
     :param lang: the language we are working in, to check against the task
     :param country: applicable countries, also for checking
    """
    if defaults is None:
        defaults = {}

    # Ensure the Pii field is a PiiEnum
    piid = task.get("pii")
    if piid is None:
        raise InvArgException("missing PiiEnum in task: {}", task.get("name"))
    elif not isinstance(piid, PiiEnum):
        try:
            task["pii"] = PiiEnum[piid.upper()]
        except KeyError as e:
            raise InvArgException("unrecognizerd PiiEnum name: {}", e)

    # Check base fields: type & spec
    if "type" not in task:
        if _is_pii_class(task.get("task")):
            task["type"] = "PiiTask"
        else:
            raise InvArgException("invalid task specification: no type field")
    if task["type"] not in ("PiiTask", "callable", "re", "regex", "regex-external"):
        raise InvArgException("unsupported task type: {}", task["type"])
    if "task" not in task:
        raise InvArgException("invalid task specification: no task field")

    # Check task spec against task type, and load object if needed
    if task["type"] == "regex-external":
        task["type"] = "regex"
        task["task"] = _import_object(task["task"])
    if task["type"] in ("re", "regex") and not isinstance(task["task"], str):
        raise InvArgException("regex spec should be a string")
    elif task["type"] == "callable":
        if isinstance(task["task"], str):
            task["task"] = _import_object(task["task"])
        if not isinstance(task["task"], Callable):
            raise InvArgException("callable spec should be a callable")
    elif task["type"] == "PiiTask":
        if isinstance(task["task"], str):
            task["task"] = _import_object(task["task"])
        if not _is_pii_class(task["task"]):
            raise InvArgException("class spec should be a PiiTask object")

    # Fill in task name
    if "name" not in task:
        name = getattr(task["task"], "pii_name", None)
        if not name:
            name = getattr(task["task"], "__name__", None)
            if name and task["type"] == "PiiTask":
                name = " ".join(re.findall(r"[A-Z][^A-Z]*", name)).lower()
            elif task["type"] == "callable":
                name = name.replace("_", " ")
        if not name:
            name = (task["type"] + " for " + task["pii"].name).lower()
        task["name"] = name

    # Fill in doc
    if "doc" not in task and not isinstance(task["task"], str):
        doc = getattr(task["task"], "__doc__", None)
        if doc:
            task["doc"] = doc.strip()

    # Process lang
    lang_task = task.get("lang")
    lang_def = defaults.get("lang")
    if lang_task is None:
        if lang_def is None:
            raise InvArgException("no lang can be determined for task {!r}", piid)
        task["lang"] = lang_def
    elif lang_def is not None and lang_task not in (lang_def, LANG_ANY):
        raise InvArgException("language mismatch in task descriptor: {} vs {}",
                              lang_task, lang_def)

    # Process country
    country_task = task.get("country")
    country_def = defaults.get("country")
    if country_task is None:
        if country_def is None:
            raise InvArgException("no country can be determined for task {!r}", piid)
        task["country"] = country_def
    elif country_def is not None and country_task not in country_def and country_task != COUNTRY_ANY:
        raise InvArgException("country mismatch in task descriptor: {} vs {}",
                              country_task, country_def)

    # Process version & source
    for f in ("version", "source"):
        if f not in task and f in defaults:
            task[f] = defaults[f]

    return task


def parse_taskdict(task: Dict, defaults: Dict = None) -> Iterable[Dict]:
    """
    Check the fields in a task descriptor. Complete missing fields, if possible
    Expand multiple-pii entries into separate dicts.
    """
    if not isinstance(task, dict):
        raise InvPiiTask("task spec is not a dictionary")
    try:
        piid = task.get("pii")
        if not isinstance(piid, List):
            # Single task
            yield _parse_taskdict(task.copy(), defaults)
        else:
            # We need to demultiplex this task, one dict per PII enum
            for p in piid:
                t = task.copy()
                t["pii"] = p
                yield _parse_taskdict(t, defaults)
    except InvPiiTask:
        raise
    except Exception as e:
        raise InvPiiTask("Error while parsing task definition: {}", e) from e


def build_tasklist(task_list: TYPE_TASK_LIST,
                   defaults: Dict = None) -> Iterable[Dict]:
    """
    Given a list of raw task definitions, build an iterable of finalized task
    dicts
      :param task_list: list of task definitions
      :param defaults: default values for task properties, if they are not
        defined in their dicts
    """
    if not isinstance(task_list, (list, tuple)):
        raise InvPiiTask("invalid tasklist: not a list/tuple")

    for src in task_list:
        # Fetch the task
        if isinstance(src, tuple):  # parse a simplified spec (a tuple)
            # Checks
            if len(src) != 2 and (len(src) != 3 or not isinstance(src[1], str)):
                raise InvPiiTask("invalid simplified task spec")
            # Task type
            task_type = ("PiiTask" if _is_pii_class(src[1])
                         else "callable" if callable(src[1])
                         else "regex" if isinstance(src[1], str)
                         else None)
            # Build the dict
            td = {"pii": src[0], "type": task_type, "task": src[1]}
            if len(src) > 2:
                td["name"] = src[2]
            yield from parse_taskdict(td, defaults)
        elif isinstance(src, dict):  # full form
            yield from parse_taskdict(src, defaults)
        else:
            raise InvPiiTask("task definition must be a tuple or dict")
