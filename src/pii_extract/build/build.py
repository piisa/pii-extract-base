"""
Build task objects
"""

from typing import Dict, Any

from pii_data.helper.exception import InvArgException

from .task import BasePiiTask, CallablePiiTask, RegexPiiTask


def is_pii_class(obj: Any) -> bool:
    """
    Return if an object is a PiiTask class object
    """
    return isinstance(obj, type) and issubclass(obj, BasePiiTask)


def build_task(taskd: Dict, debug: bool = False) -> BasePiiTask:
    """
    Build a task object from its task definition
      :param taskd: a task definition (i.e. a *parsed* task descriptor)
    """
    # Prepare standard arguments
    try:
        odef = taskd["obj"]
        tclass, tobj = odef["class"], odef["task"]
        base_args = {"task": taskd["info"], "pii": taskd["piid"]}
    except KeyError as e:
        raise InvArgException("invalid final taskd: missing field {}", e)

    # Extra custom arguments
    # (class & regex: for the constructor; callable: for the callable itself)
    extra_kwargs = odef.get("kwargs", {})

    # Create the task object
    if tclass == "piitask":
        proc = tobj(**base_args, **extra_kwargs, debug=debug)
    elif tclass == "callable":
        proc = CallablePiiTask(tobj, **base_args, extra_kwargs=extra_kwargs,
                               debug=debug)
    elif tclass in ("re", "regex"):
        proc = RegexPiiTask(tobj, **base_args, **extra_kwargs, debug=debug)
    else:
        raise InvArgException("invalid pii task type for {}: {}",
                              taskd["piid"].get("pii"), tclass)
    return proc
