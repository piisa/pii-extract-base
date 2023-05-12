from collections.abc import Iterable as AbcIterable

from typing import Dict, Iterable

from pii_data.types import PiiEnum

from pii_extract.defs import LANG_ANY
from pii_extract.build import is_pii_class
from pii_extract.helper.utils import taskd_field
from pii_extract.gather.parser import defs
from pii_extract.gather.parser.utils import InvPiiTask
from ..utils import piid_ok

# ------------------------------------------------------------------------


def normalize_rawtaskd(raw: defs.TYPE_TASKD) -> Dict:
    """
    Ensure a raw task descriptor is a dictionary with a "pii" field
    """
    # A full descriptor
    if isinstance(raw, dict):

        # Ensure the PII field is a list of dicts
        piid = raw.get("pii")
        if isinstance(piid, dict):
            ent_data = [piid]
        elif isinstance(piid, (str, PiiEnum)):
            ent_data = [{"type": piid, **raw}]
        elif isinstance(piid, (list, tuple, AbcIterable)):
            return raw
        else:
            raise InvPiiTask("invalid pii field type: {}", type(piid))
        raw["pii"] = ent_data
        return raw

    # A simplified descriptor. First check it
    if len(raw) != 2 and (len(raw) != 3 or not isinstance(raw[2], str)):
        raise defs.InvPiiTask("invalid simplified task spec")

    # Task class
    task_class = ("PiiTask" if is_pii_class(raw[1])
                  else "callable" if callable(raw[1])
                  else "regex" if isinstance(raw[1], str)
                  else None)
    # Build the dict
    td = {
        defs.FIELD_CLASS: task_class,
        defs.FIELD_IMP: raw[1],
        "pii": [{"type": raw[0]}]
    }
    if len(raw) > 2:
        td["pii"][0]["subtype"] = raw[2]
    return td


# ------------------------------------------------------------------------

def _add_defaults(orig: Dict, defaults: Dict) -> Dict:
    return {**defaults, **orig}


class RawTaskDefaults:
    """
    A class to add defaults to missing fields in a raw task descriptor
    """

    def __init__(self, defaults: Dict = None, normalize: bool = True,
                 languages: Iterable[str] = None):
        """
          :param defaults: fields to add to the descriptor if they are missing
          :param normalize: ensure the descriptor is a proper dict
          :param languages: restrict task descriptors to those languages
        """
        self._norm = normalize
        self._lang = set(languages) if languages else None
        if defaults is None:
            defaults = {}
        self._piid = {k: v for k, v in defaults.items()
                      if k in ("lang", "country")}
        self._info = {k: v for k, v in defaults.items()
                      if k in ("source", "version")}


    def __call__(self, raw_list: Iterable[Dict]) -> Iterable[Dict]:
        """
        Normalize and add defaults to a list of tasks
        """
        for raw in raw_list:
            if self._lang:
                lang = raw.get("lang") or raw.get("pii", {}).get("lang")
                if lang != LANG_ANY and lang not in self._lang:
                    continue
            if self._norm:
                raw = normalize_rawtaskd(raw)
            if self._info:
                raw.update((k, v) for k,v in self._info.items() if k not in raw)
            if self._piid:
                piid = raw["pii"]
                if isinstance(piid, dict):      # not normalized
                    raw["pii"] = _add_defaults(piid, self._piid)
                else:
                    raw["pii"] = [_add_defaults(p, self._piid) for p in piid]
            yield raw
