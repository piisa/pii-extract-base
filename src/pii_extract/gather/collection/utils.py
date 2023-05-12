"""
Utilities to manage elements inside task definitions
"""

from typing import Dict, List, Union, Set

from pii_data.helper.exception import InvArgException
from pii_data.types import PiiEnum

from ...helper.utils import taskd_field


TYPE_TASKENUM = Union[PiiEnum, List[PiiEnum], str, List[str]]
TYPE_PIID = Union[Dict, List[Dict]]


# --------------------------------------------------------------------------


def ensure_enum(pii: Union[str, PiiEnum]) -> PiiEnum:
    """
    Ensure a task specification is a PiiEnum
    """
    try:
        return pii if isinstance(pii, PiiEnum) else PiiEnum[str(pii).upper()]
    except KeyError:
        raise InvArgException("unknown pii type: {}", pii)


def ensure_enum_list(pii: TYPE_TASKENUM) -> List[PiiEnum]:
    """
    Ensure a task specification is a list of PiiEnum
    """
    if isinstance(pii, (list, tuple)):
        return [ensure_enum(t) for t in pii]
    else:
        return [ensure_enum(pii)]


def piid_ok(piid: Dict, lang: Set[str], country: Set[str],
            pii: Set[PiiEnum]) -> bool:
    """
    Decide if a PII descriptor agrees with a type/language/country filter
    """
    if pii and not pii & taskd_field(piid, "pii"):
        return False

    if lang and not lang & taskd_field(piid, "lang"):
        return False

    # Country is different: the task descriptor may not have it
    if country:
        task_country = taskd_field(piid, "country")
        if task_country and not country & task_country:
            return False

    return True


def filter_piid(piid: TYPE_PIID, lang: Set[str], country: Set[str] = None,
                pii: Set[PiiEnum] = None) -> TYPE_PIID:
    """
    Select from a (possibly multiple) PII descriptor the items that agree with
    a PiiEnum/language/country filter
    """
    if not lang and not country and not pii:
        return piid

    if isinstance(piid, dict):
        return piid if piid_ok(piid, lang, country, pii) else None
    else:
        return [p for p in piid if piid_ok(p, lang, country, pii)]
