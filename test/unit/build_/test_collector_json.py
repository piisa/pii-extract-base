"""
Test the JsonTaskCollector class
"""

from pathlib import Path
import json

from typing import Dict, Iterable

from pii_data.types import PiiEnum
from pii_extract.defs import LANG_ANY, COUNTRY_ANY
from pii_extract.build.task import BasePiiTask

import pii_extract.build.collector.json as mod

from taux.modules.en.any.international_phone_number import PATTERN_INT_PHONE


_TASKFILE = Path(__file__).parents[2] / "data" / "task-spec.json"



# ---------------------------------------------------------------------

def test100_lang_file():
    """
    Check the list of languages, add config file
    """
    tc = mod.JsonTaskCollector()
    tc.add_tasks(_TASKFILE)
    got = tc.language_list()
    assert [LANG_ANY, "en"] == got


def test110_lang_dict():
    """
    Check the list of languages, add dict of task
    """
    with open(_TASKFILE, encoding="utf-8") as f:
        tasks = json.load(f)

    tc = mod.JsonTaskCollector()
    tc.add_tasks(tasks)
    got = tc.language_list()
    assert [LANG_ANY, "en"] == got


def test120_gather_all_lang():
    """
    """
    tc = mod.JsonTaskCollector()
    tc.add_tasks(_TASKFILE)

    got = list(tc.gather_all_tasks(LANG_ANY))
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.CREDIT_CARD

    got = list(tc.gather_all_tasks("en"))
    assert len(got) == 1
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER

    got = list(tc.gather_all_tasks(["en", LANG_ANY]))
    assert len(got) == 2
    assert got[0]["pii"] == PiiEnum.PHONE_NUMBER
    assert got[1]["pii"] == PiiEnum.CREDIT_CARD

    got = list(tc.gather_all_tasks(["en", LANG_ANY, "es"]))
    assert len(got) == 2

    got = list(tc.gather_all_tasks(["es"]))
    assert len(got) == 0


def test130_gather_all():
    """
    """
    tc = mod.JsonTaskCollector()
    tc.add_tasks(_TASKFILE)

    got = list(tc.gather_all_tasks())
    assert len(got) == 2

    exp = {
        'pii': PiiEnum.PHONE_NUMBER,
        'type': 'regex',
        'task': PATTERN_INT_PHONE,
        'name': 'international phone number',
        'doc': 'detect phone numbers that use international notation. Uses context',
        'context': {'value': ['ph', 'phone', 'fax'],
                    'width': [16, 0], 'type': 'word'},
        'lang': 'en',
        'country': 'any',
        "version": "0.0.1",
        "source": "piisa:pii-extract-base:test"
    }
    assert exp == got[1]

