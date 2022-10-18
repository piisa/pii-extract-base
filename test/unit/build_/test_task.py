import pytest

from pii_data.types import PiiEnum, PiiEntity, DocumentChunk
from pii_extract.helper.exception import PiiUnimplemented

import pii_extract.build.task as mod


def test10_base():
    """
    Create base object
    """
    task_spec = {"pii": PiiEnum.BITCOIN_ADDRESS, "lang": "es", "name": "example"}
    task = mod.BasePiiTask(**task_spec)
    assert task.pii == PiiEnum.BITCOIN_ADDRESS
    assert task.lang == "es"
    assert task.name == "example"

    chunk = DocumentChunk("1", "blah")
    with pytest.raises(PiiUnimplemented):
        task(chunk)


def test20_regex():
    """
    Test regex object
    """
    task_spec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es", "name": "example"}
    task = mod.RegexPiiTask(r"\d{4}", **task_spec)

    chunk = DocumentChunk("1", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity(PiiEnum.CREDIT_CARD, "1234", "1", 7, name="example"),
        PiiEntity(PiiEnum.CREDIT_CARD, "3451", "1", 23, name="example"),
    ]
    assert exp == got


def test21_regex_group():
    """
    Test regex object, capturing group
    """
    task_spec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es", "name": "example"}
    task = mod.RegexPiiTask(r"number\s(\d{4})", **task_spec)

    chunk = DocumentChunk("1", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity(PiiEnum.CREDIT_CARD, "1234", "1", 7, name="example"),
        PiiEntity(PiiEnum.CREDIT_CARD, "3451", "1", 23, name="example"),
    ]
    assert exp == got


def test30_callable():
    """
    Test callable object
    """

    def example(i: str):
        return ["1234", "3451"]

    task_spec = {"pii": PiiEnum.CREDIT_CARD, "lang": "es", "name": "example"}
    task = mod.CallablePiiTask(example, **task_spec)

    chunk = DocumentChunk("abc", "number 1234 and number 3451")
    got = list(task(chunk))
    exp = [
        PiiEntity(PiiEnum.CREDIT_CARD, "1234", "abc", 7, name="example"),
        PiiEntity(PiiEnum.CREDIT_CARD, "3451", "abc", 23, name="example"),
    ]
    assert exp == got


def test40_class():
    """
    Test class object
    """

    exp = [
        PiiEntity(PiiEnum.CREDIT_CARD, "1234", "abc", 7, name="example"),
        PiiEntity(PiiEnum.CREDIT_CARD, "3451", "abc", 23, name="example"),
    ]

    class ExampleClass(mod.BasePiiTask):
        def find(self, chunk):
            return exp

    task = ExampleClass(pii=PiiEnum.CREDIT_CARD, lang="any")

    chunk = DocumentChunk("abc", "number 1234 and number 3451")
    got = list(task(chunk))
    assert exp == got
