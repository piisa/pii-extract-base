"""
Build task objects
"""

from typing import Dict

from pii_data.helper.exception import InvArgException

from .task import BasePiiTask, CallablePiiTask, RegexPiiTask


def build_task(taskd: Dict) -> BasePiiTask:
    """
    Build a task object from its task definition
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
        proc = tobj(**base_args, **extra_kwargs)
    elif tclass == "callable":
        proc = CallablePiiTask(tobj, **base_args, extra_kwargs=extra_kwargs)
    elif tclass in ("re", "regex"):
        proc = RegexPiiTask(tobj, **base_args, **extra_kwargs)
    else:
        raise InvArgException("invalid pii task type for {}: {}",
                              taskd["piid"].get("pii"), tclass)
    return proc
