"""
Define the CallablePiiTask subclass
"""

from typing import Iterable, Callable

from pii_data.types import PiiEntity
from pii_data.types.doc import DocumentChunk

from .base import BasePiiTask


class CallablePiiTask(BasePiiTask):
    """
    A wrapper for a PII implemented as a function
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
        Call the function, get all returned strings, and locate them in the
        passed document to generate the Pii objects
        """
        defaults = self.get_pii_defaults()
        for cc in self.call(chunk.data, **self.kwargs):
            start = 0
            while True:
                pos = chunk.data.find(cc, start)
                if pos < 0:
                    break
                yield PiiEntity(self.pii_info, cc, chunk.id, pos, **defaults)
                start = pos + len(cc)
