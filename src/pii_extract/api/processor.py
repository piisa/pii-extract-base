"""
Definition of the main PiiProcessor object: a class that 
 * creates a PiiTaskCollection and fills it with tasks definitions
 * uses it to build task objects
 * and applies the objects to documents
 * creating a PiiCollection with the results.
"""

import logging
from collections import defaultdict

from typing import Tuple, List, Dict, Iterable, Union

from pii_data.types import PiiEntityInfo, PiiEntity, PiiDetector, PiiCollection
from pii_data.types.doc import SrcDocument, DocumentChunk
from pii_data.helper.exception import ProcException

from ..helper.logger import PiiLogger
from ..gather.collector import JsonTaskCollector
from ..build.task import PiiTaskInfo
from ..build.collection import get_task_collection, TYPE_TASKENUM


class PiiCollectionBuilder(PiiCollection):
    """
    A small varianto of the PiiCollection class, in which the add() method
    accepts a PiiTaskInfo object instead of a PiiDetector, and builds it
    """

    def add(self, pii: PiiEntity, info: Union[PiiTaskInfo, Dict], method: str):
        """
         :param pii: the detected Pii entity
         :param info: a PiiTaskInfo (or equivalent dict) for the task that
           did the detection
        """
        if isinstance(info, PiiTaskInfo):
            info = info.asdict()
        kwargs = {k: info.get(k) for k in ("source", "name", "version")}
        detector = PiiDetector(**kwargs, method=method)
        super().add(pii, detector)



# --------------------------------------------------------------------------


class PiiProcessor:

    def __init__(self, config: Dict = None, skip_plugins: bool = False,
                 debug: bool = False):
        """
        Initialize a PII Processor object
          :param config: configuration file, possibly containing a
            "pii-extract:tasks" section and/or a "pii-extract:plugins" section
          :param skip_plugins: skip loaginf pii-extract plugins
        """
        self._debug = debug
        self._log = PiiLogger(__name__, debug)
        self._tasks = None
        self._stats = {"num": defaultdict(int), "entities": defaultdict(int)}
        self._ptc = get_task_collection(load_plugins=not skip_plugins,
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
                    pii: TYPE_TASKENUM = None, add_any: bool = True) -> int:
        """
        Build a set of tasks
         :param lang: language to build tasks for
         :param country: countri(es) to build task for; if unspecified all
            possible countries will be built
         :param tasks: a specific set of pii types to build detectors for
            (otherwise build all available types)
         :param add_any: when setting a specific lang and/or country, add also
            tasks valid for "any"
        """
        # Sanitize input
        self._lang = lang.lower() if lang else None
        self._log(". Build tasks: %s", lang)
        if isinstance(country, str):
            country = [country]
        self._country = [c.lower() for c in country] if country else None
        # Build the list of tasks
        tasks = self._ptc.build_tasks(self._lang, self._country,
                                      pii=pii, add_any=add_any)
        self._tasks = list(tasks)
        return len(self._tasks)


    def task_info(self) -> Dict[Tuple, Tuple]:
        """
        Return a dictionary with all the instantiated tasks:
          - keys are tuples (task id, subtype)
          - values are lists of tuples (country, task name, task doc)
        """
        if self._tasks is None:
            raise ProcException("no detector tasks have been built")

        info = defaultdict(list)
        for t in self._tasks:
            pii_list = t.pii_info
            if isinstance(pii_list, PiiEntityInfo):
                pii_list = [pii_list]
            for pii in pii_list:
                info[(pii.pii, pii.subtype)].append(
                    (pii.country, t.task_info.name, t.task_info.doc)
                )
        return info


    def detect_chunk(self, chunk: DocumentChunk,
                     piic: PiiCollectionBuilder) -> int:
        """
        Process a document chunk, calling all defined processors and performing
        PII extraction
          :param chunk: document chunk to analyze
          :param piic: collection to add the detected PII instances to
        """
        self._log("... Detect chunk=%s", chunk.id, level=logging.DEBUG)
        if self._tasks is None:
            raise ProcException("no built detector tasks")

        processed = set()
        num = 0
        for task in self._tasks:

            # See if we have already applied this task to the chunk
            if task in processed:
                continue
            processed.add(task)

            # Execute the task
            for pii in task(chunk):
                if "process" not in pii.fields:
                    pii.fields["process"] = {"stage": "detection"}
                piic.add(pii, task.task_info, task.get_method(pii.info))

                num += 1
                self._stats["num"]["entities"] += 1
                self._stats["entities"][pii.info.pii.name] += 1

        return num


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
        self._log(".. Detect document=%s", doc.id)

        self._stats["num"]["calls"] += 1

        piicol = PiiCollectionBuilder(lang=self._lang, docid=doc.id)
        for chunk in doc.iter_full(context=chunk_context):
            self.detect_chunk(chunk, piicol)

        return piicol


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
