"""
Define the base classes for Pii Tasks
"""

from dataclasses import dataclass, fields

from typing import Iterable, Dict, Any, List

from pii_data.helper.misc import filter_dict
from pii_data.helper.exception import InvArgException
from pii_data.types import PiiEntityInfo, PiiEntity
from pii_data.types.doc import DocumentChunk

from ...helper.exception import PiiUnimplemented
from ...helper.normalizer import normalize
from ...helper.context import context_spec, context_check



def dbg_task(typ: str, *info: List[PiiEntityInfo], out=None):
    """
    Print out a brief task description
    """
    print(f".. Task{typ if typ else ''}:", end=" ", file=out)
    for p in info:
        print(f"{p.pii.name}/{p.lang}/{p.country}", end=" ", file=out)
    print(file=out)


def dbg_item(value: str, out=None):
    """
    Print out a found result
    """
    print(f"... found: [{value}]", file=out)


# --------------------------------------------------------------------------

@dataclass(order=True)
class PiiTaskInfo:
    """
    A class to hold all information about a PiiTask
    """
    source: str = None
    name: str = None
    version: str = None
    method: str = None
    doc: str = None


    def asdict(self) -> Dict:
        """
        Return as a dictionary, but without the empty fields
        """
        d = {k: v for (k, v) in map(lambda f: (f.name, getattr(self, f.name)),
                                    fields(self))}
        return filter_dict(d)


# --------------------------------------------------------------------------

class BasePiiTask:
    """
    Base class for a Pii Detector Task
.   """

    def __init__(self, task: Dict, pii: Dict, debug: bool = False):
        """
        Base constructor
          :param task: a task info dictionary
          :param pii: a PII descriptor dictionary
        """
        #print("INIT", task, pii)

        if not isinstance(pii, dict):
            raise InvArgException("invalid pii argument to PiiTask")
        if task is None:
            task = {}

        # Add context & method
        self.method = pii.get("method") or task.get("method")
        context = pii.get("context")
        self.context = context_spec(context) if context else None

        # Fetch the options to be stored in the info subobject
        pii_info = {k: v for k, v in pii.items()
                    if k not in ("method", "extra", "context")}

        # Store options
        self.pii_info = PiiEntityInfo(**pii_info)
        self.task_info = PiiTaskInfo(**task)
        self.debug = debug


    def get_method(self, pii: Any, **kwargs):
        """
        Return the 'method' metadata field
        """
        return self.method


    def get_pii_defaults(self) -> Dict:
        """
        Get a dictionary with defaults for a PiiTask Instance
        """
        defaults = {"name": self.task_info.name, "country": self.pii_info.country}
        return defaults


    def check_context(self, text: str, pii: PiiEntity, prefix: int = 0) -> bool:
        """
        Check that a pii candidate has the required context around it
        """
        return context_check(text, self.context,
                             [prefix + pii.pos, prefix + pii.pos + len(pii)],
                             debug=self.debug)


    def find_context(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        Wrap over the standard find() method and filter out the occcurences
        that do not match the desired context around them
        """
        ndoc = None
        for pii in self.find(chunk):

            # Extract the text to search the context in
            if ndoc is None:

                # Enlarge with the neighboring chunks, if they are available
                if chunk.context:
                    bf = chunk.context.get("before", "")
                    fulltext = bf + chunk.data + chunk.context.get("after", "")
                    prefix = len(bf)
                else:
                    fulltext = chunk.data
                    prefix = 0

                # Normalize (lowercase) the text for the context
                lang = pii.info.lang
                ndoc = normalize(fulltext, lang, lowercase=True)

            # Check if the context is there
            if self.check_context(ndoc, pii, prefix):
                yield pii


    def find(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        **Method to be implemented in subclasses**
        """
        raise PiiUnimplemented("missing implementation for Pii Task")


    def __call__(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        Perform Pii extraction on a document chunk
        """
        mth = self.find_context if self.context else self.find
        return mth(chunk)


    def __repr__(self) -> str:
        """
        Return a string with a representation for the task
        """
        return f"<{self.__class__.__name__}:{self.task_info.name} [{self.pii_info.lang}/{self.pii_info.country}]>"
