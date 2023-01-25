"""
Build collections of tasks
"""

from typing import Dict, List, Iterable, Union, Set

from pii_data.helper.exception import InvArgException
from pii_data.types import PiiEnum

from ...defs import LANG_ANY, COUNTRY_ANY
from ...gather.collector.base import BaseTaskCollector
from ...gather.parser import parse_task_descriptor
from ...helper.utils import field_set, taskd_field, union_sets
from ..task import BasePiiTask
from ..build import build_task


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
    Decide if a PII descriptor agrees with a language/country filter
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


# --------------------------------------------------------------------------


class PiiTaskCollection:
    """
    The object holding the set of task descriptors, which can then be
    instantiated into task objects
    """

    def __init__(self):
        """
        """
        self._tasks = []
        self._lang = None
        self._countries = None
        self._num = 0


    def __repr__(self) -> str:
        return f"<PiiTaskCollection #{self._num}>"


    def __len__(self) -> int:
        """
        Return the number of gathered tasks
        """
        return self._num


    def add_collector(self, tc: BaseTaskCollector) -> int:
        """
        Fetch all raw tasks descriptors gathered by a task collector,
        convert them to task definitions and add them to the list
        """
        self._lang = self._countries = None
        num = 0
        for num, taskd in enumerate(tc.gather_tasks(), start=1):
            self._tasks.append(parse_task_descriptor(taskd))
        self._num += num
        return num


    def language_list(self) -> List[str]:
        """
        Return all languages with defined tasks
        """
        if self._lang is None:
            self._lang = union_sets(taskd_field(t["piid"], "lang")
                                    for t in self._tasks)
        return self._lang


    def country_list(self) -> List[str]:
        """
        Return all languages with defined tasks
        """
        if self._countries is None:
            self._countries = union_sets(taskd_field(t["piid"], "country")
                                         for t in self._tasks)
        return self._countries


    def taskdef_list(self, lang: Iterable[str] = None,
                     country: Iterable[str] = None, pii: TYPE_TASKENUM = None,
                     add_any: bool = True) -> Iterable[Dict]:
        """
        Return specific task(s) for a given language., PII type(s) & countries

        Try to find the most specific task available, using the specs:
          :param lang: language to search, if not specified search tasks for all
            languages
          :param country: country to search, if not specified all countries
            will be searched
          :param pii: task enum type(s) to select
          :param add_any: if False,
              - do not add "any" lang tasks, except if explicitly requested
              - do not add "any" country tasks, unless explicitly requested or
                all languages have been requested
          :return: an iterable of task definitions
        """
        # Consolidate filters
        if lang:
            lang = field_set(lang)
            if add_any:
                lang.add(LANG_ANY)
        if country:
            country = field_set(country)
            if add_any:
                country.add(COUNTRY_ANY)
        pii = set(ensure_enum_list(pii)) if pii is not None else None

        # Traverse the task list and apply the filters
        for taskd in self._tasks:

            # If no lang/country filter, we're done
            if not lang and not country and not pii:
                yield taskd
                continue

            # Filter by language and/or country and/or PII
            piid = filter_piid(taskd["piid"], lang, country, pii)
            if not piid:
                continue
            elif isinstance(piid, dict) or len(piid) == len(taskd["piid"]):
                yield taskd
            else:
                yield {"obj": taskd["obj"], "info": taskd["info"], "piid": piid}


    def build_tasks(self, lang: str = None, country: Iterable[str] = None,
                    pii: TYPE_TASKENUM = None,
                    add_any: bool = True) -> Iterable[BasePiiTask]:
        """
        Build a list of tasks from their definitions stored in the collection.
        Return the list of built task objects.
        """
        # Get the list of tasks to build
        tasklist = self.taskdef_list(lang, country, pii=pii, add_any=add_any)

        # Build and return them
        built = set()
        for td in tasklist:
            if td["obj"]["task"] in built:
                continue  # we don't build the same task twice
            task = build_task(td)
            if task:
                built.add(td["obj"]["task"])
                yield task
