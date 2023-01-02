import pytest

from pii_data.types import PiiEnum, PiiEntity, PiiEntityInfo
from pii_data.types.doc import DocumentChunk

from pii_extract.build.task.regex import RegexPiiTask
import pii_extract.build.task.multi as mod


class MyMultiPiiTask(mod.BaseMultiPiiTask):

    def __init__(self):
        tinfo = {"source": "unit-test", "name": "mymultitask1"}
        super().__init__(tinfo)
        t1 = {"pii": PiiEnum.BLOCKCHAIN_ADDRESS, "lang": "any"}
        t2 = {"pii": PiiEnum.CREDIT_CARD, "lang": "any"}
        self.add_pii_info(t1)
        self.add_pii_info(t2)
        self.t = [RegexPiiTask(r"BC\d\d\d\d", task=None, pii=t1),
                  RegexPiiTask(r"\d\d\d\d\d", task=None, pii=t2)]

    def find(self, chunk: DocumentChunk):
        for task in self.t:
            yield from task(chunk)


class MyMultiPiiTaskContext(mod.BaseMultiPiiTask):

    def __init__(self):
        tinfo = {"source": "unit-test", "name": "mymultitask2"}
        super().__init__(tinfo)
        t1 = {"pii": PiiEnum.BLOCKCHAIN_ADDRESS, "lang": "any"}
        t2 = {"pii": PiiEnum.CREDIT_CARD, "lang": "any", "context": "credit"}
        self.add_pii_info(t1)
        self.add_pii_info(t2)
        self.t = [RegexPiiTask(r"BC\d\d\d\d", task=None, pii=t1),
                  RegexPiiTask(r"\d\d\d\d\d", task=None, pii=t2)]

    def find(self, chunk: DocumentChunk):
        for task in self.t:
            yield from task(chunk)


# --------------------------------------------------------------------------


def test10_base():
    """
    Create base object
    """
    task_spec = {"source": "test-unit", "name": "example", "version": "0.0"}
    task = mod.BaseMultiPiiTask(task=task_spec, pii=None)

    exp = mod.PiiTaskInfo(**task_spec)
    assert task.task_info == exp


def test11_base():
    """
    Create base object, with entity info
    """
    task_spec = {"source": "test-unit", "name": "example", "version": "0.0"}
    pii_spec = {"pii": PiiEnum.BLOCKCHAIN_ADDRESS, "lang": "es"}
    task = mod.BaseMultiPiiTask(task=task_spec, pii=pii_spec)

    exp = mod.PiiTaskInfo(**task_spec)
    assert task.task_info == exp

    exp = PiiEntityInfo(**pii_spec)
    got = task.get_pii_info(pii=PiiEnum.BLOCKCHAIN_ADDRESS, lang="es")
    assert exp == got
    assert got.pii == PiiEnum.BLOCKCHAIN_ADDRESS
    assert got.lang == "es"


def test12_base():
    """
    Create base object, add_info
    """
    task_spec = {"source": "test-unit", "name": "example", "version": "0.0"}
    task = mod.BaseMultiPiiTask(task=task_spec, pii=None)

    ent_spec = {"pii": PiiEnum.BLOCKCHAIN_ADDRESS, "lang": "es", "country": "mx"}
    task.add_pii_info(ent_spec)

    exp = mod.PiiTaskInfo(**task_spec)
    assert task.task_info == exp

    exp = PiiEntityInfo(**ent_spec)
    got = task.get_pii_info(pii=PiiEnum.BLOCKCHAIN_ADDRESS, lang="es",
                            country="mx")
    assert exp == got


def test20_obj():
    """
    Create a multi object
    """
    task = MyMultiPiiTask()

    exp = mod.PiiTaskInfo(source="unit-test", name="mymultitask1")
    assert exp == task.task_info

    exp = [
        PiiEntityInfo(PiiEnum.CREDIT_CARD, lang="any"),
        PiiEntityInfo(PiiEnum.BLOCKCHAIN_ADDRESS, lang="any")
    ]
    assert exp == sorted(task.pii_info)


def test21_obj():
    """
    Use a multi object
    """
    task = MyMultiPiiTask()

    chunk = DocumentChunk(
        "1", "This is a bitcoin BC3421 and this is a credit card 12345"
    )

    got = list(task(chunk))
    assert len(got) == 2
    assert got == [PiiEntity.build(PiiEnum.BLOCKCHAIN_ADDRESS, "BC3421", "1", 18),
                   PiiEntity.build(PiiEnum.CREDIT_CARD, "12345", "1", 51)]


def test22_obj_context():
    """
    Use a multi object, context
    """
    task = MyMultiPiiTaskContext()

    chunk = DocumentChunk(
        "1", "This is a bitcoin BC3421 and this is a credit card 12345"
    )

    got = list(task(chunk))
    assert len(got) == 2
    assert got == [PiiEntity.build(PiiEnum.BLOCKCHAIN_ADDRESS, "BC3421", "1", 18),
                   PiiEntity.build(PiiEnum.CREDIT_CARD, "12345", "1", 51)]


def test23_obj_context():
    """
    Use a multi object, context
    """
    task = MyMultiPiiTaskContext()

    chunk = DocumentChunk(
        "1", "This is a bitcoin BC3421 and this is a card 12345"
    )

    # Now we don't have the credit card context, so we whouldn't detect it
    got = list(task(chunk))
    assert len(got) == 1
    assert got == [PiiEntity.build(PiiEnum.BLOCKCHAIN_ADDRESS, "BC3421", "1", 18)]
