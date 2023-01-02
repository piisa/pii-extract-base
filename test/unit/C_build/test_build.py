"""
Test the build_task function with finalized task descriptors
"""

import pytest

from pii_data.helper.exception import InvArgException

from pii_extract.build.task import BasePiiTask, CallablePiiTask, RegexPiiTask
import pii_extract.build.build as mod

import taux.examples_task_descriptor_full as TASKD


# -------------------------------------------------------------------------

def test100_build_regex():
    """
    Test building a PiiTask regex
    """
    task = mod.build_task(TASKD.TASK_PHONE_NUMBER)
    assert isinstance(task, RegexPiiTask)


def test110_build_callable():
    """
    Test building a callable PiiTask
    """
    task = mod.build_task(TASKD.TASK_GOVID)
    assert isinstance(task, CallablePiiTask)


def test120_build_class():
    """
    Test building a PiiTask
    """
    task = mod.build_task(TASKD.TASK_CREDIT_CARD)
    assert isinstance(task, BasePiiTask)


def test200_build_err():
    """
    Test building an invalid PiiTask
    """
    with pytest.raises(InvArgException):
        mod.build_task(TASKD.TASK_ERR)
