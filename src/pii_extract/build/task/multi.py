"""
Define the BaseMultiPiiTask base subclass
"""

from typing import Union, Dict, List, Iterable

from pii_data.types import PiiEnum, PiiEntityInfo, PiiEntity

from ...helper.exception import InvArgException
from ...helper.context import context_spec, context_check
from .base import PiiTaskInfo, BasePiiTask

TYPE_KEY = Union[PiiEnum, PiiEntityInfo]


def _key(info: TYPE_KEY, lang: str = None, country: str = None,
         subtype: str = None, **kwargs) -> str:
    """
    Return the key to locate the info for one task
    """
    if isinstance(info, PiiEntityInfo):
        return info.pii, info.subtype, info.lang, info.country
    elif isinstance(info, PiiEnum):
        return info, subtype, lang, country
    else:
        raise InvArgException("invalid field for taskinfo: {}", type(info))


class BaseMultiPiiTask(BasePiiTask):
    """
    A variant base task that can detect more than one PII type
    Note that the "find" method must be provided by a subclass
    """

    def __init__(self, task: Dict, pii: List[Dict] = None, debug: bool = False):
        """
        Base constructor.
         :param task: task basic information
         :param pii: list of entities this task detects
        """
        # print("INIT", task, pii)
        self.debug = debug
        self.task_info = PiiTaskInfo(**(task or {}))
        self.context = {}
        self.method = {}
        self._pii_info = {}
        if pii:
            self.add_pii_info(pii)


    def __repr__(self) -> str:
        """
        Return a string with a representation for the task
        """
        return f"<{self.__class__.__name__}:{self.task_info.name}>"


    @property
    def pii_info(self) -> Iterable[PiiEntityInfo]:
        """
        Provide an iterable with all PII Info fields
        """
        return self._pii_info.values()


    def add_pii_info(self, pii: Union[Dict, List]):
        """
        Add Pii info sets
        """
        if isinstance(pii, dict):
            pii = [pii]

        for ent in pii:
            ent.pop("extra", None)
            context = ent.pop("context", None)
            method = ent.pop("method", self.task_info.method)
            pii_info = PiiEntityInfo(**ent)
            key = _key(pii_info)

            # Add context & method
            if method:
                self.method[key] = method
            if context:
                self.context[key] = context_spec(context)

            # Add entity info
            self._pii_info[key] = pii_info


    def get_method(self, pii: TYPE_KEY, **kwargs) -> str:
        """
        Return the 'method' metadata field for a given pii element
        """
        key = _key(pii, **kwargs)
        try:
            return self.method[key]
        except KeyError:
            raise InvArgException("no method in multitask for {}", key)


    def get_pii_info(self, pii: TYPE_KEY, **kwargs) -> PiiEntityInfo:
        """
        Get a Pii info set for a given pii element
        """
        key = _key(pii, **kwargs)
        try:
            return self._pii_info[key]
        except KeyError:
            raise InvArgException("no PII info in multitask for {}", key)


    def check_context(self, text: str, pii: PiiEntity, prefix: int = 0) -> bool:
        """
        Check that a pii candidate has the required context around it
        """
        key = _key(pii.info.pii, lang=pii.info.lang,
                   country=pii.fields.get("country"))
        ctx = self.context.get(key)
        if not ctx:
            return True
        return context_check(text, ctx,
                             [prefix + pii.pos, prefix + pii.pos + len(pii)])
