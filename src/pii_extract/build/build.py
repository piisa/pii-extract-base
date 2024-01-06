"""
Build task objects
"""

from typing import Dict, Any

from pii_data.helper.exception import InvArgException

from .task import BasePiiTask, CallablePiiTask, RegexPiiTask, dbg_msg


def is_pii_class(obj: Any) -> bool:
    """
    Return if an object is a PiiTask class object
    """
    return isinstance(obj, type) and issubclass(obj, BasePiiTask)


def find_task_config(config: Dict, base_args: Dict) -> Dict:
    """
    Find a custom config for the task, matching on task name and, optionally,
    source and version
    """
    if config is None:
        return None
    config = config.get("task_config")
    if config is None:
        return None

    info = base_args["task"]
    tname = info["name"]
    config = [c for c in config if c["name"] == tname]
    if not config:
        return None

    tsource = info["source"]
    config = [c for c in config if c.get("source") in (tsource, None)]
    if not config:
        return None

    tversion = info["version"]
    config = [c for c in config if c.get("version") in (tversion, None)]

    return config[0].get("config") if config else None


def build_task(taskd: Dict, config: Dict = None,
               debug: bool = False) -> BasePiiTask:
    """
    Build a task object from its task definition
      :param taskd: a task definition (i.e. a *parsed* task descriptor)
      :param config: task custom configuration to apply
      :param debug: activate debug mode
    """
    # Prepare standard arguments from the task definition
    try:
        odef = taskd["obj"]
        tclass, tobj = odef["class"], odef["task"]
        base_args = {"task": taskd["info"], "pii": taskd["piid"]}
    except KeyError as e:
        raise InvArgException("invalid final taskd: missing field {}", e)

    # Extra custom arguments
    # (class & regex: for the constructor; callable: for the callable itself)
    extra_kwargs = odef.get("kwargs", {})

    # Find custom config for this task
    config = find_task_config(config, base_args)
    if debug and config:
        dbg_msg(".. building {}: config found", taskd["info"].get("name"))

    # Create the task object
    if tclass == "piitask":
        proc = tobj(**base_args, **extra_kwargs, config=config, debug=debug)
    elif tclass == "callable":
        proc = CallablePiiTask(tobj, **base_args, extra_kwargs=extra_kwargs,
                               config=config, debug=debug)
    elif tclass in ("re", "regex"):
        proc = RegexPiiTask(tobj, **base_args, **extra_kwargs,
                            config=config, debug=debug)
    else:
        raise InvArgException("invalid pii task type for {}: {}",
                              taskd["piid"].get("pii"), tclass)
    return proc
