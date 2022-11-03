"""
Define the base classes for Pii Tasks
"""

import regex
from typing import Iterable, Callable

from pii_data.types import DocumentChunk, PiiEntity

from ..helper.normalizer import normalize
from ..helper.context import context_spec, context_check, CONTEXT_NORM_OPTIONS
from ..helper.exception import PiiUnimplemented


NORM_OPTIONS = dict(whitespace=True, lowercase=True)


# --------------------------------------------------------------------------

class BasePiiTask:
    """
    Base class for a Pii Detector Task
    """

    def __init__(self, **kwargs):
        """
        Base constructor: fetch & store all generic parameters
        """
        # print("INIT", kwargs)
        # Full set
        self.options = kwargs.copy()
        # Compulsory fields
        for f in ("pii", "lang"):
            setattr(self, f, kwargs.pop(f))
        # Optional fields
        for f in ("country", "name", "version", "source"):
            setattr(self, f, kwargs.pop(f, None))
        # Documentation
        self.doc = kwargs.pop("doc", self.pii.name)
        # Context
        context = kwargs.pop("context", None)
        self.context = context_spec(context) if context else None


    def check_context(self, text: str, pii: PiiEntity, prefix: int = 0) -> bool:
        """
        Check that a pii candidate has the required context around it
        """
        return context_check(text, self.context,
                             [prefix + pii.pos, prefix + pii.pos + len(pii)])


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

                # Normalize the text
                ndoc = normalize(fulltext, self.lang, **CONTEXT_NORM_OPTIONS)

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
        return f"<{self.pii.name}:{self.name}:{self.country}:{self.__class__.__qualname__}>"


# --------------------------------------------------------------------------


class RegexPiiTask(BasePiiTask):
    """
    A wrapper for a PII implemented as a regex pattern
    Instead of the standard re package it uses the regex package (in
    backwards-compatible mode)
    """

    def __init__(self, pattern: str, **kwargs):
        super().__init__(**kwargs)
        self.regex = regex.compile(pattern, flags=regex.X | regex.VERSION0)

    def find(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        Iterate over the regex and produce Pii objects
        """
        for cc in self.regex.finditer(chunk.data):
            g = 1 if cc.lastindex is not None else 0
            yield PiiEntity(self.pii, cc.group(g), chunk.id, cc.start(g),
                            name=self.name, country=self.country)


# --------------------------------------------------------------------------


class CallablePiiTask(BasePiiTask):
    """
    A wrapper for a PII implemented as a function
    """

    def __init__(self, call: Callable, extra_kwargs=None, **kwargs):
        super().__init__(**kwargs)
        self.call = call
        self.kwargs = extra_kwargs or {}

    def find(self, chunk: DocumentChunk) -> Iterable[PiiEntity]:
        """
        Call the function, get all returned strings, and locate them in the
        passed document to generate the Pii objects
        """
        for cc in self.call(chunk.data, **self.kwargs):
            start = 0
            while True:
                pos = chunk.data.find(cc, start)
                if pos < 0:
                    break
                yield PiiEntity(self.pii, cc, chunk.id, pos,
                                name=self.name, country=self.country)
                start = pos + len(cc)
