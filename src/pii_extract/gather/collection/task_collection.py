"""
Build collections of task definitions
"""

from typing import Dict, List, Iterable, Union

from pii_data.helper.logger import PiiLogger

from ...defs import LANG_ANY, COUNTRY_ANY
from ...helper.utils import field_set, taskd_field, union_sets
from ...build.task import BasePiiTask
from ...build import build_task
from ..parser import parse_task_descriptor
from .sources.base import BaseTaskCollector
from .utils import ensure_enum_list, filter_piid, TYPE_TASKENUM


def is_lang_any(piid: Union[List, Dict]) -> bool:
    """
    See if a PII definition (or a list of them) is for the "any" language
    """
    if isinstance(piid, dict):
        return piid["lang"] == LANG_ANY
    else:
        return any(t["lang"] == LANG_ANY for t in piid)


class PiiTaskCollection:
    """
    An object holding a set of task definitions, which can then be
    instantiated into task objects
    """

    def __init__(self, debug: bool = False):
        """
        """
        self._log = PiiLogger(__name__, debug)
        self._debug = debug
        self._lang = None       # languages with collected tasks
        self._countries = None  # countries with collected tasks
        self._built = {}        # all built tasks
        self.task_def = []      # list of task definitions collected


    def __repr__(self) -> str:
        return f"<PiiTaskCollection #{len(self)}>"


    def __len__(self) -> int:
        """
        Return the number of gathered tasks definitions
        """
        return len(self.task_def)


    def num(self, built: bool = False) -> int:
        """
        Return the number of tasks, either
          - the number available task definitions
          - the number of built task objects
        """
        return len(self._built) if built else len(self.task_def)


    def add_collector(self, tc: BaseTaskCollector) -> int:
        """
        Fetch all raw tasks descriptors gathered by a task collector,
        convert them to task definitions and add them to the object list
        """
        # Reset list of languages/countries so that they will be computed again
        self._lang = self._countries = None

        # Append all tasks gathered by the collector
        self._log(". gather-tasks from: %s", tc)
        num = 0
        for num, taskd in enumerate(tc.gather_tasks(), start=1):
            self.task_def.append(parse_task_descriptor(taskd))
        return num


    def language_list(self) -> List[str]:
        """
        Return all languages that have task definitions
        """
        if self._lang is None:
            self._lang = union_sets(taskd_field(t["piid"], "lang")
                                    for t in self.task_def)
        return self._lang


    def country_list(self) -> List[str]:
        """
        Return all countries that have task descriptors
        """
        if self._countries is None:
            self._countries = union_sets(taskd_field(t["piid"], "country")
                                         for t in self.task_def)
        return self._countries


    def taskdef_list(self, lang: Iterable[str] = None,
                     country: Iterable[str] = None, pii: TYPE_TASKENUM = None,
                     add_any: bool = True) -> Iterable[Dict]:
        """
        Return specific task(s) for a given language, PII type(s) & countries

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

        # Traverse the list of task definitions and apply the filters
        for taskd in self.task_def:

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
        Build and return a list of tasks from their definitions stored in
        the collection.
          :param lang: select tasks to build for these languages
          :param country: select tasks to build for these countries
          :param country: select tasks to build for these PII types
          :param add_any: when restricting language/country, add also language-
             and country-independent tasks
          :return: an iterable yielding the built task objects.

        """
        # Get the list of tasks to build
        tasklist = self.taskdef_list(lang, country, pii=pii, add_any=add_any)

        # Build and return them
        for td in tasklist:

            # Define a language-specific identifier for the task
            langid = LANG_ANY if is_lang_any(td["piid"]) else lang
            objid = f"{langid}-{id(td['obj']['task'])}"

            # Build it, if we don't have it yet
            if objid not in self._built:
                task = build_task(td, debug=self._debug)
                self._built[objid] = task

            # Deliver it
            yield self._built[objid]
