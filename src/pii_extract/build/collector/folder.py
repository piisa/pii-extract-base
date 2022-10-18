"""
Build lists of PiiTask specifications by traversing a folder
"""

import importlib
from pathlib import Path

from typing import Dict, List, Iterable


from ...defs import LANG_ANY, COUNTRY_ANY
from ..parser import build_tasklist
from .base import BaseTaskCollector

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


# --------------------------------------------------------------------------


class FolderTaskCollector(BaseTaskCollector):

    def __init__(self, pkg: str, basedir: Path, source: str,
                 version: str = None, debug: bool = False):
        """
          :param pkg: basename for the package
          :param basedir: base directory where the task implementations are
          :param source: source for the tasks (vendor/organization/package)
          :param version: task version
          :param debug: print out debug information
        """
        super().__init__(debug=debug)
        self.basedir = Path(basedir)
        self._debug = debug
        self._pkg = pkg
        self._defaults = {'source': source or pkg}
        if version:
            self._defaults['version'] = version


    @property
    def name(self):
        return self._pkg


    def _gather_tasks(self, name: str, path: str, lang: str,
                      country: str) -> Iterable[Dict]:
        """
        Import and load all the tasks defined in a Python module
        """
        pkg = f"{self._pkg}.{name}"
        self._dbgout("... PII TASKS for", pkg)
        self._dbgout("... path =", path)

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

        # Get all the tasks defined in those files
        num = 0
        for mname in sorted(modlist):
            mod = importlib.import_module("." + mname, pkg)
            task_list = getattr(mod, _LISTNAME, None)
            if not task_list:
                continue

            for task in build_tasklist(task_list, defaults):
                yield task
                self._dbgout("   {} -> ({}) {}",
                             task['pii'].name, task['type'], task.get("doc"))
                num += 1

        if num == 0:
            self._dbgout("... NO PII TASKS for", pkg)


    def language_list(self) -> List[str]:
        """
        Return all languages defined in the package
        """
        return mod_subdir(self.basedir)


    def country_list(self, lang: str = None) -> List[str]:
        """
        For a given language, return all countries with defined tasks
        """
        # A specific language
        if lang is not None:
            return mod_subdir(self.basedir / lang)
        # All languages
        country = set()
        for lang in self.language_list():
            country.update(self.country_list(lang))
        return sorted(country)


    def gather_tasks(self, lang: str, country: str = None) -> Iterable[Dict]:
        """
        Import all task processors available for a given lang & country
        """
        self._dbgout(".. IMPORT FROM:", lang, "/", country)
        if lang == LANG_ANY:
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
