"""
Base class to create TaskCollector objects
"""

import sys

from typing import Dict, List, Iterable

from ...helper.types import TYPE_STR_LIST


# --------------------------------------------------------------------------


class BaseTaskCollector:
    """
    The base class to define objects for collecting PII Task implementations

    Subclasses need to implement _gather_tasks()
    They can also reimplement language_list(), country_list() and/or
    gather_tasks(), if it can be made more efficient.
    """

    def __init__(self, debug: bool = False):
        """
          :param pkg: basename for the package
          :param basedir: base directory where the task implementations are
          :param debug: print out debug information
        """
        self._debug = debug
        self._country = None


    def _dbgout(self, msg: str, *args, **kwargs):
        if self._debug:
            file = kwargs.pop("file", sys.stderr)
            print(msg.format(*args), file=file, **kwargs)


    def language_list(self) -> List[str]:
        """
        Return all languages defined
        """
        lang = set(t["lang"] for t in self._gather_tasks())
        return sorted(lang)


    def country_list(self, lang: str = None) -> List[str]:
        """
        Return the list of available countries
        """
        country = set(t["country"] for t in self._gather_tasks()
                      if not lang or t["lang"] == lang)
        return sorted(country)


    def gather_tasks(self, lang: str, country: str = None) -> Iterable[Dict]:
        """
        Import all task processors available for a given lang & country
        Needs a _gather_tasks() method in the subclass
        """
        # Get an iterator over all available tasks
        tasklist = self._gather_tasks()

        # All languages & countries
        if not lang and not country:
            yield from iter(tasklist)
            return

        # Specific language(s)
        if isinstance(lang, str):
            lang = [lang]
        if lang:
            lang = set(lang)

        # Specific country(s)
        if isinstance(country, str):
            country = [country]
        if country:
            country = set(country)

        for task in tasklist:
            if (lang and task.get("lang") not in lang or
                country and task.get("country") not in country):
                continue
            yield task


    def gather_all_tasks(self, lang: TYPE_STR_LIST = None) -> Iterable[Dict]:
        """
        Build and return an iterable with all gathered tasks
         :param lang: list of languages for which tasks are searched for. If
           not passed, all languages available will be gathered
        """
        if lang is None:
            lang = self.language_list()
        elif isinstance(lang, str):
            lang = [lang]
        if self._debug:
            self._dbgout(". GATHER LANGUAGES: {}", " ".join(sorted(lang)))

        for ln in lang:
            yield from self.gather_tasks(ln, None)
