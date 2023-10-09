"""
Define the CallablePiiTask subclass
"""

from typing import Iterable, Callable

from pii_data.types import PiiEntity
from pii_data.types.doc import DocumentChunk

from .base import BasePiiTask, dbg_task, dbg_item


class CallablePiiTask(BasePiiTask):
    """
    A wrapper for a PII detector implemented as a function.
    Since it inherits from BasePiiTask, it will automatically apply context
    validation to the function results, if a suitable context argument is added
    """

    def __init__(self, call: Callable, extra_kwargs=None, **kwargs):
        """
         :param call: callable to execute
         :param extra_kwargs: additional keywords arguments to pass to their
           callable
        """
        super().__init__(**kwargs)
        self.call = call
        self.kwargs = extra_kwargs or {}


    def find(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        Call the function, get all returned strings, and if needed locate them
        in the passed document to generate the Pii objects
        """
        kwargs = self.get_pii_defaults()
        if self.debug:
            dbg_task("Cll", self.pii_info)
        for cc in self.call(chunk.data, **self.kwargs):

            if self.debug:
                dbg_item(cc if isinstance(cc, str) else cc[0])

            # If we're given a tuple, it's (string, position); we can create
            # the PiiEntity and move on
            if isinstance(cc, tuple):
                yield PiiEntity(self.pii_info, cc[0], chunk.id, cc[1], **kwargs)
                continue

            # Else it's a string; we need to _find_ its position(s)
            start = 0
            while True:
                pos = chunk.data.find(cc, start)
                if pos < 0:
                    break
                yield PiiEntity(self.pii_info, cc, chunk.id, pos, **kwargs)
                start = pos + len(cc)
