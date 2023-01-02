import pytest

from pii_data.types import PiiEnum, PiiEntity
from pii_data.types.doc import DocumentChunk
from pii_extract.helper.exception import PiiUnimplemented

import pii_extract.build.task as mod


def test100_taskinfo():
    """
    Create taskinfo object
    """
    task_spec = {"source": "unit-test", "name": "example"}
    info = mod.PiiTaskInfo(**task_spec)

    assert info.source == "unit-test"
    assert info.name == "example"
    assert info.version is None
    assert info.doc is None


def test110_taskinfo_dict():
    """
    Taskinfo object as dictionary
    """
    task_spec = {"source": "unit-test", "name": "example"}
    info = mod.PiiTaskInfo(**task_spec)
    assert task_spec == info.asdict()


def test200_base():
    """
    Create base object
    """
    
    task_spec = {"name": "example"}
    pii_spec = {"pii": PiiEnum.BLOCKCHAIN_ADDRESS, "lang": "es"}
    task = mod.BasePiiTask(task_spec, pii_spec)
    assert task.pii_info.pii == PiiEnum.BLOCKCHAIN_ADDRESS
    assert task.pii_info.lang == "es"
    assert task.task_info.name == "example"

    chunk = DocumentChunk("1", "blah")
    with pytest.raises(PiiUnimplemented):
        task(chunk)


def test210_regex():
    """
    Test regex object
    """
    task_spec = {"name": "example"}
    pii_spec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es"}
    task = mod.RegexPiiTask(r"\d{4}", task=task_spec, pii=pii_spec)

    chunk = DocumentChunk("1", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity.build(PiiEnum.CREDIT_CARD, "1234", "1", 7, name="example"),
        PiiEntity.build(PiiEnum.CREDIT_CARD, "3451", "1", 23, name="example"),
    ]
    assert exp == got


def test220_regex_group():
    """
    Test regex object, capturing group
    """
    task_spec = {"name": "example"}
    pii_spec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es"}
    task = mod.RegexPiiTask(r"number\s(\d{4})", task=task_spec, pii=pii_spec)

    chunk = DocumentChunk("1", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity.build(PiiEnum.CREDIT_CARD, "1234", "1", 7, name="example"),
        PiiEntity.build(PiiEnum.CREDIT_CARD, "3451", "1", 23, name="example"),
    ]
    assert exp == got


def test230_callable():
    """
    Test callable object
    """

    def example_callable(i: str):
        return ["1234", "3451"]

    tspec = {"name": "example"}
    pspec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es"}
    task = mod.CallablePiiTask(example_callable, task=tspec, pii=pspec)

    chunk = DocumentChunk("abc", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity.build(PiiEnum.CREDIT_CARD, "1234", "abc", 7, name="example"),
        PiiEntity.build(PiiEnum.CREDIT_CARD, "3451", "abc", 23, name="example"),
    ]
    assert exp == got


def test240_class():
    """
    Test class object
    """
    exp = [
        PiiEntity.build(PiiEnum.CREDIT_CARD, "1234", "abc", 7, name="example"),
        PiiEntity.build(PiiEnum.CREDIT_CARD, "3451", "abc", 23, name="example")
    ]

    class ExampleClass(mod.BasePiiTask):
        def find(self, chunk):
            return exp
    
    pii = {"pii": PiiEnum.CREDIT_CARD, "lang": "any"}
    task = ExampleClass(pii=pii, task=None)

    chunk = DocumentChunk("abc", "number 1234 and number 3451")
    got = list(task(chunk))
    assert exp == got
