"""
Build lists of PiiTask descriptors by traversing folders
"""

import importlib
from pathlib import Path
from itertools import chain

from typing import Dict, List, Iterable

from pii_data.types import PiiEnum
from pii_data.helper.exception import ConfigException

from pii_extract.defs import LANG_ANY, COUNTRY_ANY
from pii_extract.helper.utils import union_sets
from pii_extract.gather.parser.defs import FIELD_CLASS
from pii_extract.gather.parser.parser import piienum
from .base import BaseTaskCollector
from .utils import RawTaskDefaults

# For folder defs: name of the Python list holding pii tasks inside a module
_LISTNAME = "PII_TASKS"


# --------------------------------------------------------------------------


def _norm(elem: str) -> str:
    """
    Strip away a final underscore in a folder name (used to avoid reserved
    Python words)
    """
    return elem[:-1] if elem.endswith("_") else elem


def mod_subdir(basedir: str) -> List[str]:
    """
    Return all module subdirectories for a given base directory
    """
    try:
        return sorted(_norm(d.name) for d in basedir.iterdir() if d.is_dir()
                      and d.name != "__pycache__")
    except FileNotFoundError:
        return []


def task_subtype(task: Dict) -> str:
    """
    Return a string deifning the task subtype, if possible
    """
    sub = (p.get("subtype") for p in task["pii"])
    sub = ([s] if isinstance(s, str) else s for s in filter(None, sub))
    sub = "/".join(chain.from_iterable(sub))
    if sub is None:
        sub = task.get("name")
    return f"({sub})" if sub else ""



# --------------------------------------------------------------------------


class FolderTaskCollector(BaseTaskCollector):

    def __init__(self, pkg: str, basedir: Path, source: str,
                 version: str = None, pii_filter: List[PiiEnum] = None,
                 languages: Iterable[str] = None, debug: bool = False):
        """
          :param pkg: basename for the package
          :param basedir: base directory where the task implementations are
          :param source: source for the tasks (vendor/organization/package)
          :param version: version for the tasks
          :param pii_filter: collect only tasks for these PII types
          :param languages: currently unused
          :param debug: print out debug information
        """
        super().__init__(languages=languages, debug=debug)
        self._pkg = pkg
        self._defaults = {'source': source or pkg}
        if version:
            self._defaults['version'] = version
        self.basedir = Path(basedir)
        self._log(".. Folder task collector (%s, version=%s): init",
                  self.__class__.__name__, version)

        # PII filter
        if not pii_filter:
            self._pii_filter = None
        else:
            try:
                self._pii_filter = set(piienum(p) for p in pii_filter)
            except Exception as e:
                raise ConfigException("invalid pii_filter in config: {}",
                                      e) from e
                self._log(".. PII filter: %s", sorted(pii_filter))



    @property
    def name(self):
        return self._pkg


    def _gather_tasks(self, name: str, path: str, lang: str,
                      country: str) -> Iterable[Dict]:
        """
        Import and load all the tasks defined in one Python module
        """
        pkg = f"{self._pkg}.{name}"
        self._log("... PII TASKS for %s", pkg)
        self._log("... path = %s", path)

        # Get the list of Python files in the module
        modlist = (m.stem for m in Path(path).iterdir()
                   if m.suffix == ".py" and not m.stem.startswith(('_', '.')))

        #print("** GATHER:", pkg, name, path, lang, country)

        # Prepare default metadata
        defaults = {
            "lang": lang,
            "country": country
        }
        defaults.update(self._defaults)
        reformat = RawTaskDefaults(defaults, normalize=True)

        # Get all the tasks defined in those files
        num = 0
        for mname in sorted(modlist):
            mod = importlib.import_module("." + mname, pkg)
            task_list = getattr(mod, _LISTNAME, None)
            if not task_list:
                continue

            #for task in build_task_descriptors(task_list, defaults):
            if isinstance(task_list, dict):
                task_list = [task_list]
            for task in reformat(task_list):
                pii = set(piienum(p.get("type")) for p in task["pii"])
                if self._pii_filter and not (pii & self._pii_filter):
                    continue
                yield task
                num += 1

                if self._debug:
                    pii = ",".join(p.name for p in sorted(pii))
                    self._log("     %s %s -> %s", pii, task_subtype(task),
                              task[FIELD_CLASS])

        if num == 0:
            self._log("... NO PII TASKS for %s", pkg)


    def language_list(self) -> List[str]:
        """
        Return all languages defined in the package
        """
        all_lang = mod_subdir(self.basedir)
        if not self._lang:
            return all_lang
        else:
            return [ln for ln in all_lang if ln in self._lang or ln == LANG_ANY]


    def country_list(self, lang: str = None) -> List[str]:
        """
        For a given language(s), return all countries with defined tasks
        """
        # A specific language
        if isinstance(lang, str):
            return mod_subdir(self.basedir / lang)

        # All languages
        if lang is None:
            lang = self.language_list()

        return union_sets(self.country_list(ln) for ln in lang)


    def gather_tasks(self, lang: str = None,
                     country: str = None) -> Iterable[Dict]:
        """
        Import all task processors available for a given lang & country
        """
        self._log(".. gather-tasks lang=%s", lang)
        self._log(".. %s import from: %s/%s", self.__class__.__name__,
                  lang, country or "<all>")
        if lang is None or not isinstance(lang, str):
            if lang is None:
                lang = self.language_list()
            for ln in lang:
                yield from self.gather_tasks(ln, country)
            return
        elif lang == LANG_ANY:
            name = LANG_ANY
            path = self.basedir / LANG_ANY
            country = COUNTRY_ANY       # any-lang tasks are also any-country
        elif country is None:
            for country in self.country_list(lang):
                yield from self.gather_tasks(lang, country)
            return
        else:
            country_subd = country + "_" if country in ("in", "is") else country
            lang_subd = lang if lang not in ("is",) else lang + "_"
            name = f"{lang_subd}.{country_subd}"
            path = self.basedir / lang_subd / country_subd

        # mod = importlib.import_module('...lang.' + name, __name__)
        yield from self._gather_tasks(name, path, lang, country)
