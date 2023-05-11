"""
Build full task definitions from raw task descriptors.
"""

import re
import importlib
from inspect import cleandoc
from dataclasses import fields as dataclass_fields

from typing import Dict, Tuple, Callable, Type, Union, Iterable, List

from pii_data.types import PiiEnum
from pii_data.helper.exception import InvArgException

from ...build import is_pii_class
from ...build.task import BasePiiTask, PiiTaskInfo
from .defs import FIELD_CLASS, FIELD_IMP
from .utils import InvPiiTask


TYPE_TASKD_LIST = Iterable[Dict]


# --------------------------------------------------------------------------

def piienum(ptype: Union[PiiEnum, str]) -> PiiEnum:
    """
    Validate a PiiEnum value
    """
    if ptype is None:
        raise InvArgException("missing PiiEnum in task descriptor")
    elif isinstance(ptype, PiiEnum):
        return ptype
    else:
        try:
            return PiiEnum[ptype.upper()]
        except KeyError as e:
            raise InvArgException("unrecognized PiiEnum: {}", e) from e


def _import_object(objname: str) -> Union[Callable, Type[BasePiiTask]]:
    try:
        modname, oname = objname.rsplit(".", 1)
        mod = importlib.import_module(modname)
        return getattr(mod, oname)
    except Exception as e:
        raise InvPiiTask("cannot import task object '{}': {}",
                         objname, e) from e


def _parse_taskdict(raw_taskd: Dict,
                    defaults: Dict = None) -> Tuple[Dict, Dict]:
    """
    Check the dict fields for a task, fill up missing fields if needed
     :param task: the raw descriptor for the task, as a dictionary
     :param defaults: default values to add if missing
     :return: a tuple (task_object_data, task_info)
    """
    info = {f: raw_taskd[f]
            for f in map(lambda df: df.name, dataclass_fields(PiiTaskInfo))
            if f in raw_taskd}

    # Check task class
    task_type = raw_taskd.get(FIELD_CLASS)
    if task_type is None:
        if is_pii_class(raw_taskd.get(FIELD_IMP)):
            task_type = "piitask"
        else:
            raise InvPiiTask("missing field: {}", FIELD_CLASS)
    task_type = str(task_type).lower()
    if task_type not in ("piitask", "callable", "re", "regex", "regex-external"):
        raise InvPiiTask("unsupported task class: {}", task_type)
    task = {FIELD_CLASS: task_type}

    # Check task implementation
    if FIELD_IMP not in raw_taskd:
        raise InvPiiTask("missing field: {}", FIELD_IMP)
    task[FIELD_IMP] = raw_taskd[FIELD_IMP]
    # Check task spec against task type, and load object if needed
    if task_type not in ("re", "regex") and isinstance(raw_taskd[FIELD_IMP], str):
        task[FIELD_IMP] = _import_object(raw_taskd[FIELD_IMP])
    else:
        task[FIELD_IMP] = raw_taskd[FIELD_IMP]

    if task_type == "regex-external":
        task[FIELD_CLASS] = "regex"

    if task[FIELD_CLASS] == "regex" and not isinstance(task[FIELD_IMP], str):
        raise InvPiiTask("regex spec should be a string")
    elif task[FIELD_CLASS] == "callable" and not isinstance(task[FIELD_IMP], Callable):
        raise InvPiiTask("callable spec should be a callable")
    elif task[FIELD_CLASS] == "piitask" and not is_pii_class(task[FIELD_IMP]):
        raise InvPiiTask("class spec should be a PiiTask object")

    if "kwargs" in raw_taskd:
        task["kwargs"] = raw_taskd["kwargs"]

    # Add source, version from defaults, if not there yet
    if defaults:
        for f in ("source", "version"):
            if f not in info and f in defaults:
                info[f] = defaults[f]

    # Fields that might also be stored in class attributes
    for f in ("name", "doc"):
        if f not in info:
            v = getattr(task[FIELD_IMP], "pii_" + f, None)
            if v:
                info[f] = v

    # Fill in description from docstring
    if "doc" not in info and not isinstance(task[FIELD_IMP], str):
        description = getattr(task[FIELD_IMP], "__doc__", None)
        if description:
            info["doc"] = cleandoc(description).strip()

    return task, info


def _parse_piidict(piid: Dict, task: Dict, defaults: Dict = None) -> Dict:
    """
    Check the dict fields for a PII, fill fields if needed
     :param piid: the descriptor for the pii in the task, as a dictionary
     :param defaults: default values to add
    """
    if not isinstance(piid, dict):
        raise InvPiiTask("pii descriptor is not a dict")

    # Start dict
    out = {f: piid[f]
           for f in ("lang", "country", "subtype", "context", "method", "extra")
           if f in piid and piid[f]}

    # Validate "type" field
    out["pii"] = piienum(piid.get("type"))

    # Add defaults if missing
    if defaults is not None:
        for f in ("lang", "country"):
            if f in defaults and f not in out:
                out[f] = defaults[f]

    # Add fields that might also be stored in class attributes
    for f in ("subtype", "method"):
        if f not in out:
            v = getattr(task[FIELD_IMP], "pii_" + f, None)
            if v:
                out[f] = v

    # Try to compose a "method" field, if possible
    if "method" not in out:
        if task[FIELD_CLASS] == "regex":
            out["method"] = "regex"
            if "context" in piid:
                out["method"] += ",context"

    # We need a "lang" attribute
    if "lang" not in out:
        raise InvPiiTask("invalid PII info set for {}: missing lang",
                         out["pii"].name)

    return out


def _build_task_name(obj_data: Dict, pii: Dict):
    """
    Build a name for a task
    """
    name = getattr(obj_data[FIELD_IMP], "__name__", None)
    if name and obj_data[FIELD_CLASS] == "piitask":
        name = " ".join(re.findall(r"[A-Z][^A-Z]*", name)).lower()
    elif name and obj_data[FIELD_CLASS] == "callable":
        name = name.replace("_", " ")
    if name:
        return name

    ent = [pii] if isinstance(pii, dict) else pii
    sall = set()
    for e in ent:
        n = e["pii"].name
        s = e.get("subtype")
        if s:
            n += ":" + s
        sall.add(n)

    return obj_data[FIELD_CLASS] + " for " + "/".join(sorted(sall))


def _demux_field(pii_list: List[Dict], field: str) -> List[Dict]:
    """
    Demultiplex a field from a PII dict that can be multiple
    """
    out = []
    for pii in pii_list:
        value = pii.get(field)

        # If not a multiple field, add the instance & continue
        if not isinstance(value, (list, tuple)):
            out.append(pii)
            continue

        # Create one instance per field value
        for s in value:
            td = pii.copy()
            td[field] = s
            out.append(td)
    return out


# --------------------------------------------------------------------------


def parse_task_descriptor(taskd: Dict, defaults: Dict = None) -> Dict:
    """
    Check the fields in a task descriptor. Complete missing fields, if possible
    Expand multiple-pii entries into separate dicts.
    """
    if not isinstance(taskd, dict):
        raise InvPiiTask("task descriptor is not a dict")

    try:
        # Get the object & info dicts
        obj_data, task_info = _parse_taskdict(taskd, defaults)
        #print("\nDATA", obj_data, task_info, taskd, sep="\n")

        # Traverse the PII information and build the PII field
        pii_data = [_parse_piidict(t, obj_data, defaults)
                    for t in taskd.get("pii")]

        # Demultiplex PII subfields than can be multiple
        for field in ("subtype", "lang", "country"):
            pii_data = _demux_field(pii_data, field)

        # If we've got a single PII element, flatten the list
        if len(pii_data) == 1:
            pii_data = pii_data[0]

        # Add a name for the task, if we do not have one yet
        if "name" not in task_info:
            task_info["name"] = _build_task_name(obj_data, pii_data)

        return {"obj": obj_data, "info": task_info, "piid": pii_data}

    except KeyError as e:
        raise InvPiiTask("task descriptor error: missing field {}", e) from e
    except Exception as e:
        raise InvPiiTask("task descriptor error: {}", e) from e
