"""
Build collections of tasks
"""

from collections import defaultdict

from typing import Dict, List, Iterable, Union

from pii_data.helper.exception import InvArgException
from pii_data.types import PiiEnum

from ..defs import LANG_ANY, COUNTRY_ANY
from ..build import BasePiiTask, CallablePiiTask, RegexPiiTask
from ..build.collector.base import BaseTaskCollector
from ..build.collector import PluginTaskCollector, JsonTaskCollector


TYPE_TASKENUM = Union[PiiEnum, List[PiiEnum], str, List[str]]


# --------------------------------------------------------------------------


def _ensure_enum(task: Union[str, PiiEnum]) -> PiiEnum:
    try:
        return task if isinstance(task, PiiEnum) else PiiEnum[str(task).upper()]
    except KeyError:
        raise InvArgException("unknown task type: {}", task)


def check_task_enum(task: TYPE_TASKENUM) -> List[PiiEnum]:
    """
    Ensure a task specification is a list of PiiEnum
    """
    if isinstance(task, (list, tuple)):
        return [_ensure_enum(t) for t in task]
    else:
        return [_ensure_enum(task)]


def build_task(task: Dict) -> BasePiiTask:
    """
    Build a task object from its task definition
    """
    # Prepare standard arguments
    try:
        ttype, tobj = task["type"], task["task"]
        args = {k: task[k] for k in ("pii", "lang", "country", "name")}
    except KeyError as e:
        raise InvArgException("invalid pii task object: missing field {}", e)
    for k in ("doc", "version", "source", "context"):
        args[k] = task.get(k)

    # Extra custom arguments
    # (class & regex: for the constructor, callable: for the callable itself)
    kwargs = task.get("kwargs", {})

    # Instantiate
    if ttype == "PiiTask":
        proc = tobj(**args, **kwargs)
    elif ttype == "callable":
        proc = CallablePiiTask(tobj, extra_kwargs=kwargs, **args)
    elif ttype in ("re", "regex"):
        proc = RegexPiiTask(tobj, **args, **kwargs)
    else:
        raise InvArgException("invalid pii task type for {}: {}",
                              task["pii"].name, ttype)
    return proc


# --------------------------------------------------------------------------


class PiiTaskCollection:
    """
    The object holding detector tasks
    """

    def __init__(self):
        """
        """
        self._tasks = defaultdict(lambda: defaultdict(list))
        self._countries = set()
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
        Add all tasks gathered by a task collector
        """
        self._countries.update(tc.country_list())
        num = 0
        for num, task in enumerate(tc.gather_all_tasks(), start=1):
            lang = task["lang"]
            country = task["country"]
            self._tasks[lang][country].append(task)
        self._num += num
        return num


    def language_list(self) -> Iterable[str]:
        """
        Return all languages with defined tasks
        """
        return self._tasks.keys()


    def taskdef_list(self, task: TYPE_TASKENUM, lang: str = None,
                     country: Iterable[str] = None,
                     add_any: bool = True) -> Iterable[Dict]:
        """
        Return specific task(s) for a given language & country

        Try to find the most specific task available, using the specs:
          :param task: task enum type(s) to select
          :param lang: language to search, if not specified all languages will
            be searched
          :param country: country to search, if not specified all countries
            will be searched
          :param add_any: if False,
              - do not add "any" lang tasks, except if explicitly requested
              - do not add "any" country tasks, unless explicitly requested or
                all languages requested
        """
        # Finalize task spec
        if task is not None:
            task = set(check_task_enum(task))

        # Select language dict(s)
        if lang is None:
            langlist = self._tasks.keys()
        else:
            langlist = [LANG_ANY] if add_any and lang != LANG_ANY else []
            if lang in self._tasks:
                langlist.append(lang)
            if not langlist:
                return

        # Select country
        if country is None:
            countrylist = self._countries
        else:
            if isinstance(country, str):
                country = [country]
            countrylist = set(country)
            if add_any:
                countrylist.add(COUNTRY_ANY)

        # Search across all countries
        for lang in sorted(langlist):
            langdict = self._tasks[lang]
            for c in sorted(countrylist):
                tasklist = langdict.get(c, [])
                for t in tasklist:
                    if task and t["pii"] not in task:
                        continue
                    yield t


    def taskdef_dict(self, lang: str = None) -> Dict:
        """
        Return the dict holding all implemented pii tasks for a language,
        or the dict containing dicts for all languages if no language is
        specified
        """
        return self._tasks if lang is None else self._tasks.get(lang)


    def build_tasks(self, lang: str = None, country: Iterable[str] = None,
                    tasks: TYPE_TASKENUM = None,
                    add_any: bool = True) -> Iterable[BasePiiTask]:
        """
        Build a list of tasks from their definitions stored in the collection.
        Return the list of built task objects.
        """
        # Get the list of tasks to build
        tasklist = self.taskdef_list(tasks, lang, country, add_any=add_any)

        # Build and return them, ensuring there are no duplicates
        built = set()
        for td in tasklist:
            if not td.get("multi_type") and td["task"] in built:
                continue
            task = build_task(td)
            if task:
                yield task
                built.add(td["task"])



# --------------------------------------------------------------------------

def get_task_collection(load_plugins: bool = True,
                        config: Dict = None,
                        debug: bool = False) -> PiiTaskCollection:
    """
    Create a task collection; collect all applicable tasks
    """
    piic = PiiTaskCollection()
    if not config:
        config = {}

    if load_plugins:
        c = PluginTaskCollector(plugin_cfg=config.get("extract_plugins"),
                                debug=debug)
        piic.add_collector(c)

    task_cfg = config.get("extract_tasks")
    if task_cfg:
        c = JsonTaskCollector(debug=debug)
        c.add_tasks(task_cfg)
        piic.add_collector(c)

    return piic
