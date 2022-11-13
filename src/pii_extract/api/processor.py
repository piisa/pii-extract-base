"""
Definition of the main PiiProcessor object: a class that 
 * creates a PiiTaskCollection and fills it with tasks definitions
 * uses it to build task objects
 * and applies the objects to documents
 * creating a PiiCollection with the results.
"""

from collections import defaultdict

from typing import Tuple, List, Dict, Iterable

from pii_data.types import SrcDocument, PiiDetector, PiiCollection
from pii_data.helper.exception import ProcException

from ..load.task_collection import get_task_collection, TYPE_TASKENUM
from ..build.collector import JsonTaskCollector


# --------------------------------------------------------------------------


class PiiProcessor:

    def __init__(self, load_plugins: bool = True, config: Dict = None,
                 debug: bool = False):
        """
        Initialize a PII Processor object
          :param load_plugins: gather tasks in all available pii-extract plugins
          :param config: configuration file, possibly containing an
            "extract_tasks" section and/or an "extract_plugins" section
        """
        self._debug = debug
        self._tasks = None
        self._stats = defaultdict(int)
        self._ptc = get_task_collection(load_plugins=load_plugins,
                                        config=config, debug=debug)


    def __repr__(self) -> str:
        return f"<PiiProcessor #{len(self._ptc)}>"


    def add_json_tasks(self, jsonfile: str):
        """
        Add all tasks defined in one JSON file
        """
        c = JsonTaskCollector(debug=self._debug)
        c.add_tasks(jsonfile)
        self._ptc.add_collector(c)


    def language_list(self) -> Iterable[str]:
        """
        Return the list of all languages with defined tasks
        """
        return sorted(self._ptc.language_list())


    def build_tasks(self, lang: str, country: List[str] = None,
                    tasks: TYPE_TASKENUM = None, add_any: bool = True) -> int:
        """
        Build a set of tasks
         :param lang: language to build tasks forced
         :param country: countri(es) to build task for; if unspecified all
            possible countries will be built
         :param tasks: a specific set of task types to build (otherwise build
            all types)
         :param add_any: when setting lang and/or country, add also tasks
            valid for "any"
        """
        # Sanitize input
        self._lang = lang.lower() if lang else None
        if isinstance(country, str):
            country = [country]
        self._country = [c.lower() for c in country] if country else None
        # Build the list of tasks
        tasks = self._ptc.build_tasks(self._lang, self._country,
                                      tasks=tasks, add_any=add_any)
        self._tasks = list(tasks)
        return len(self._tasks)


    def task_info(self) -> Dict[Tuple, Tuple]:
        """
        Return a dictionary with all defined tasks:
          - keys are tuples (task id, country)
          - values are tuples (name, doc)
        """
        if self._tasks is None:
            raise ProcException("no detector tasks have been built")

        info = defaultdict(list)
        for task in self._tasks:
            info[(task.pii, task.country)].append((task.name, task.doc))
        return info


    def detect(self, doc: SrcDocument,
               chunk_context: bool = False) -> PiiCollection:
        """
        Process a document, calling all defined processors and performing
        PII extraction
          :param doc: document to analyze
          :param chunk_context: when iterating over the document, add contexts
            to chunks
        """
        if self._tasks is None:
            raise ProcException("no built detector tasks")

        self._stats["calls"] += 1

        piic = PiiCollection(lang=self._lang, docid=doc.id)
        for chunk in doc.iter_full(context=chunk_context):
            for task in self._tasks:
                det = PiiDetector(task.name, task.version, task.source)
                for pii in task(chunk):
                    pii.fields["status"] = "detected"
                    piic.add(pii, det)
                    self._stats[pii.type.name] += 1
                    self._stats['entities'] += 1
        return piic


    def __call__(self, doc: SrcDocument, **kwargs) -> PiiCollection:
        """
        Process a document, calling all built tasks
        """
        return self.detect(doc, **kwargs)


    def get_stats(self) -> Dict:
        """
        Get statistics over processing calls
        """
        return self._stats
