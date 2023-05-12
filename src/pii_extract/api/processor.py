"""
Definition of the main PiiProcessor object: a class that
 * creates a PiiTaskCollection and fills it with tasks definitions
 * uses it to build task objects
 * and applies the objects to documents
 * creating a PiiCollection with the results.
"""

import logging
from collections import defaultdict
from itertools import chain

from typing import Tuple, List, Dict, Iterable, Union

from pii_data.types import PiiEntityInfo, PiiEntity, PiiDetector, PiiCollection
from pii_data.types.doc import SrcDocument, DocumentChunk
from pii_data.helper.exception import ProcException, InvArgException

from ..helper.logger import PiiLogger
from ..build.task import PiiTaskInfo
from ..gather.collection import get_task_collection, TYPE_TASKENUM
from ..gather.collection.sources import JsonTaskCollector



TYPE_LANG = Union[str, Iterable[str]]

def check_language(lang1: TYPE_LANG, lang2: TYPE_LANG) -> bool:
    """
    Check language compatibility
    """
    if lang1 is None or lang2 is None:
        return True
    if isinstance(lang1, str):
        lang1 = [lang1]
    if isinstance(lang2, str):
        lang2 = [lang2]
    return bool(set(lang1) & set(lang2))



class PiiCollectionBuilder(PiiCollection):
    """
    A small variant of the PiiCollection class, with a couple of additional
    convenience methods to add PiiEntity instances
      - add_detector_fields(), which accepts a PiiTaskInfo object instead of a
        PiiDetector, and builds the PiiDetector
      - add_collection(), which adds all pii in a collection to another
    """

    def add_detector_fields(self, pii: PiiEntity,
                            info: Union[PiiTaskInfo, Dict], method: str = None):
        """
        Add a detector, given its fields
         :param pii: the detected Pii entity
         :param info: a PiiTaskInfo (or equivalent dict) for the task that
           did the detection
         :param method: task detector method, if not found in `info`
        """
        if isinstance(info, PiiTaskInfo):
            info = info.asdict()
        kwargs = {k: info.get(k)
                  for k in ("source", "name", "version", "method")}
        if method:
            kwargs["method"] = method
        detector = PiiDetector(**kwargs)
        super().add(pii, detector)


    def add_collection(self, piic: PiiCollection) -> int:
        """
        Add all PiiEntity instances in a collection to another.
        If needed, add also the detectors
        """
        num = 0
        for num, pii in enumerate(piic, start=1):
            self.add(pii, piic.get_detector(pii.fields["detector"]))
        return num


# --------------------------------------------------------------------------


class PiiProcessor:

    def __init__(self, config: Dict = None, skip_plugins: bool = False,
                 languages: Iterable[str] = None, debug: bool = False):
        """
        Initialize a PII Processor object
          :param config: configuration file, possibly containing a
            "pii-extract:tasks" section and/or a "pii-extract:plugins" section
          :param skip_plugins: skip loaginf pii-extract plugins
          :param languages: define all languages that will be used
        """
        self._debug = debug
        self._log = PiiLogger(__name__, debug)
        self._tasks = {}
        self._stats = {"num": defaultdict(int), "entities": defaultdict(int)}
        self._ptc = get_task_collection(load_plugins=not skip_plugins,
                                        languages=languages,
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
        Return the list of all languages that have available tasks
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
         :return: the number of tasks obtained
        """
        # Sanitize input
        lang = lang.lower() if lang else None
        self._log(". Build tasks: %s", lang)
        if isinstance(country, str):
            country = [country]
        self._country = [c.lower() for c in country] if country else None
        # Build the list of tasks
        tasks = self._ptc.build_tasks(lang, self._country,
                                      pii=pii, add_any=add_any)
        self._tasks[lang] = list(tasks)
        return len(self._tasks[lang])


    def task_info(self, lang: str = None) -> Dict[Tuple, Tuple]:
        """
        Return a dictionary with all the instantiated tasks:
          - keys are tuples (task id, subtype)
          - values are lists of tuples (language, country, task name, task doc)
        """
        if not self._tasks:
            raise ProcException("no detector tasks have been built")
        elif lang and lang not in self._tasks:
            raise InvArgException("no detector tasks have been built for {}", lang)

        tasklist = self._tasks[lang] if lang else chain.from_iterable(self._tasks.values())

        out = defaultdict(list)
        tset = set()
        for t in tasklist:

            tid = id(t)
            if tid in tset:
                continue
            tset.add(tid)

            pii_info_list = t.pii_info
            if isinstance(pii_info_list, PiiEntityInfo):
                pii_info_list = [pii_info_list]
            for info in pii_info_list:
                out[(info.pii, info.subtype)].append(
                    (info.lang, info.country,
                     t.task_info.name, t.task_info.doc)
                )
        return out


    def detect_chunk(self, chunk: DocumentChunk, piic: PiiCollectionBuilder,
                     default_lang: str = None) -> int:
        """
        Process a document chunk, calling all defined processors and performing
        PII extraction
          :param chunk: document chunk to analyze
          :param piic: collection to add the detected PII instances to
          :param default_lang: language to use, if the chunk does not define one
        """
        self._log("... Detect chunk=%s", chunk.id, level=logging.DEBUG)
        if not self._tasks:
            raise ProcException("no built detector tasks")

        # Select the list of tasks to apply, based on the chunk language
        lang = (chunk.context or {}).get("lang") or default_lang
        if lang:
            tasks = self._tasks.get(lang, [])
        else:
            if len(self._tasks) > 1:
                raise InvArgException("must select a language for tasks")
            tasks = next(iter(self._tasks.values()))

        piilist = []
        processed = set()
        for task in tasks:

            # See if we have already applied this task to the chunk
            if task in processed:
                continue
            processed.add(task)

            # Execute the task, and process all detected entities
            for pii in task(chunk):
                if "process" not in pii.fields:
                    pii.fields["process"] = {"stage": "detection"}
                piilist.append((pii, task.task_info, task.get_method(pii.info)))
                self._stats["num"]["entities"] += 1
                self._stats["entities"][pii.info.pii.name] += 1

        # Add all entities to the collection, sorted by position in chunk
        for pii in sorted(piilist, key=lambda p: p[0].pos):
            piic.add_detector_fields(*pii)

        return len(piilist)


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

        meta = doc.metadata
        lang = meta.get("main_lang") or meta.get("lang")
        if not lang and len(self._tasks) == 1:
            lang = next(iter(self._tasks))
        elif not check_language(lang, self._tasks.keys()):
            raise InvArgException("incompatible document language for extraction")

        piicol = PiiCollectionBuilder(lang=lang, docid=doc.id)
        for chunk in doc.iter_full(context=chunk_context):
            self.detect_chunk(chunk, piicol, default_lang=lang)

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
