"""
Test the main classes in taskdict: TaskColllector & PiiTaskCollection
"""
from pathlib import Path

from unittest.mock import Mock
import pytest

from pii_data.types import PiiEnum, PiiCollection, PiiEntity
from pii_data.types.doc import LocalSrcDocumentFile, DocumentChunk
from pii_data.helper.exception import ProcException, InvArgException
from pii_data.helper.config import load_config

from pii_extract.build.task import PiiTaskInfo
import pii_extract.defs as defs
import pii_extract.api.processor as mod

from taux import auxpatch


DATADIR = Path(__file__).parents[2] / "data"
CONFIGFILE = DATADIR / "tasklist-example.json"
DOCUMENT = DATADIR / "minidoc-example.yaml"


@pytest.fixture
def fixture_timestamp(monkeypatch):
    auxpatch.patch_timestamp(monkeypatch)

@pytest.fixture
def fixture_entry_points(monkeypatch):
    auxpatch.patch_entry_points(monkeypatch)


# -------------------------------------------------------------------------

def test100_constructor():
    """
    Test base constructor
    """
    pd = mod.PiiProcessor(skip_plugins=True)
    assert str(pd) == '<PiiProcessor #0>'


def test110_constructor_plugin(fixture_entry_points):
    """
    Test constructor, with plugins
    """
    pd = mod.PiiProcessor()
    assert str(pd) == '<PiiProcessor #3>'
    pd = mod.PiiProcessor(skip_plugins=True)
    assert str(pd) == '<PiiProcessor #0>'


def test110_constructor_json():
    """
    Test constructor, with JSON
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    assert str(pd) == '<PiiProcessor #2>'

    pd = mod.PiiProcessor(skip_plugins=True)
    pd.add_json_tasks(CONFIGFILE)
    assert str(pd) == '<PiiProcessor #2>'


def test120_constructor_plugin_json(fixture_entry_points):
    """
    Test constructor, with plugins & JSON
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(config=config)
    assert str(pd) == '<PiiProcessor #5>'

    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    assert str(pd) == '<PiiProcessor #2>'

    # Specify plugins to load
    config = load_config(CONFIGFILE)
    config[defs.FMT_CONFIG_PLUGIN] = {
        "plugins": {
            "piisa-detectors-mock-plugin-1": {"load": False}
        }
    }
    pd = mod.PiiProcessor(config=config)
    assert str(pd) == '<PiiProcessor #2>'

    # Specify plugins to load
    config = load_config(CONFIGFILE)
    config[defs.FMT_CONFIG_PLUGIN] = {
        "plugins": {
            "piisa-detectors-mock-plugin-1": {"load": True}
        }
    }
    pd = mod.PiiProcessor(config=config)
    assert str(pd) == '<PiiProcessor #5>'


def test130_language_list(fixture_entry_points):
    """
    Test language list
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(config=config)
    assert str(pd) == '<PiiProcessor #5>'
    assert list(pd.language_list()) == ["any", "en"]


def test150_task_info():
    """
    Test task_info with no tasks built
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    with pytest.raises(ProcException) as excinfo:
        pd.task_info()
    assert "no detector tasks have been built" == str(excinfo.value)


def test160_collectionbuilder():
    """
    Test PiiCollectionBuilder
    """
    pc1 = mod.PiiCollectionBuilder(lang="en")

    tinfo = PiiTaskInfo("unit test", "example", "0.0.1")
    ent = PiiEntity.build(PiiEnum.CREDIT_CARD, "0101", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb1")
    ent = PiiEntity.build(PiiEnum.PHONE_NUMBER, "1234", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb2")

    assert len(pc1) == 2
    ent = list(pc1)[0]
    assert ent.fields["detector"] == 1
    det = pc1.get_detector(1)
    assert det.fields["name"] == "example"
    assert det.fields["method"] == "blurb1"


def test161_collectionbuilder():
    """
    Test PiiCollectionBuilder
    """
    pc1 = mod.PiiCollectionBuilder(lang="en")

    tinfo = PiiTaskInfo("unit test", "example", "0.0.1")
    ent = PiiEntity.build(PiiEnum.CREDIT_CARD, "0101", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb1")
    ent = PiiEntity.build(PiiEnum.PHONE_NUMBER, "1234", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb2")

    pc2 = mod.PiiCollectionBuilder(lang="en")
    tinfo = PiiTaskInfo("unit test", "example2", "0.1.0")
    ent = PiiEntity.build(PiiEnum.CREDIT_CARD, "0101", "1", 23)
    pc2.add_detector_fields(ent, tinfo, "blurb1")
    ent = PiiEntity.build(PiiEnum.PHONE_NUMBER, "1234", "1", 23)
    pc2.add_detector_fields(ent, tinfo, "blurb2")

    pc1.add_collection(pc2)

    assert len(pc1) == 4
    ent = list(pc1)[3]
    assert ent.fields["detector"] == 2
    det = pc1.get_detector(1)
    assert det.fields["name"] == "example"
    assert det.fields["method"] == "blurb1"


def test162_collectionbuilder_clone():
    """
    Test PiiCollectionBuilder cloning
    """
    pc1 = mod.PiiCollectionBuilder(lang="en")

    # Add one PII, one detector
    tinfo = PiiTaskInfo("unit test", "example1", "0.0.1")
    ent = PiiEntity.build(PiiEnum.CREDIT_CARD, "0101", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb1")

    # Add 2nd PII, 2nd detector
    tinfo = PiiTaskInfo("unit test", "example2", "0.0.1")
    ent = PiiEntity.build(PiiEnum.PHONE_NUMBER, "1234", "1", 23)
    pc1.add_detector_fields(ent, tinfo, "blurb2")

    # Clone into a new one (keeping detectors)
    pc2 = mod.PiiCollectionBuilder.clone(pc1)
    assert len(pc2.get_detectors()) == 2

    # Add 3rd PII, reusing the last detector
    ent = PiiEntity.build(PiiEnum.CREDIT_CARD, "0101", "1", 23)
    pc2.add_detector_fields(ent, tinfo, "blurb2")

    # Add 4th PII, with a new detector
    tinfo = PiiTaskInfo("unit test", "example3", "0.1.0")
    ent = PiiEntity.build(PiiEnum.PHONE_NUMBER, "1234", "1", 23)
    pc2.add_detector_fields(ent, tinfo, "blurb3")

    assert len(pc2) == 2
    assert len(pc2.get_detectors()) == 3

    # Add PIIC objects. Should not increment the number of detectors
    pc2.add_collection(pc1)

    assert len(pc2) == 4
    assert len(pc2.get_detectors()) == 3


def test200_build_tasks():
    """
    Test building tasks
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    n = pd.build_tasks("en")
    assert n == 2
    n = pd.build_tasks("any")
    assert n == 1
    n = pd.build_tasks("en", add_any=False)
    assert n == 1


def test210_tasks_info():
    """
    Test fetching task info
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")
    exp = {
        (PiiEnum.CREDIT_CARD, None): [
            ('any', 'any', 'standard credit card',
             'Unit test credit card number detection', 'regex,checksum')
        ],
        (PiiEnum.PHONE_NUMBER, 'international phone number'): [
            ('en', 'any', 'regex for PHONE_NUMBER:international phone number',
             'Unit test international phone number [regex-external]', 'regex,context')
        ]
    }
    #print(got)
    got = pd.task_info()
    assert exp == got

    got = pd.task_info("en")
    assert exp == got

    with pytest.raises(InvArgException):
        pd.task_info("es")


def test220_tasks_detect(fixture_timestamp):
    """
    Test running a detection
    """
    DOCUMENT = Path(__file__).parents[2] / "data" / "minidoc-example.yaml"

    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    r = pd.detect(doc)
    assert isinstance(r, PiiCollection)


def test230_tasks_detect_header(fixture_timestamp):
    """
    Test the header in the produced collection
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    r = pd.detect(doc)

    exp = {
        "date": "2045-01-30",
        "format": "piisa:pii-collection:v1",
        "lang": "en",
        "stage": "detection",
        "detectors": {
            1: {
                "name": "regex for PHONE_NUMBER:international phone number",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1",
                "method": "regex,context"
            },
            2: {
                "name": "standard credit card",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1",
                "method": "regex,checksum"
            }
        }
    }
    assert exp == r.header()


def test240_tasks_detect_pii(fixture_timestamp):
    """
    Test PII detection results
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    r = pd.detect(doc)
    assert len(r) == 2

    pii = list(r)
    assert str(pii[0]) == "<PiiEntity PHONE_NUMBER:+34983453999>"
    assert str(pii[1]) == "<PiiEntity CREDIT_CARD:4273 9666 4581 5642>"


def test250_tasks_detect_pii_dict(fixture_timestamp):
    """
    Test PII detection, full dict results
    """
    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    r = pd.detect(doc)

    pii = list(r)
    assert len(pii) == 2
    exp = {
        'detector': 1,
        'type': 'PHONE_NUMBER',
        'subtype': 'international phone number',
        'process': {
            'stage': 'detection'
        },
        'value': '+34983453999',
        'chunkid': '3',
        'country': 'any',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 44,
        'end': 56
    }
    assert exp == pii[0].asdict()

    exp = {
        'detector': 2,
        'process': {
            'stage': 'detection'
        },
        'type': 'CREDIT_CARD',
        'value': '4273 9666 4581 5642',
        'chunkid': '4',
        'subtype': 'standard credit card',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 25,
        'end': 44
    }
    assert exp == pii[1].asdict()


def test250_tasks_detect_pii_config(fixture_timestamp):
    """
    Test PII detection, custom config
    """
    config = load_config([CONFIGFILE, DATADIR / "task-config.json"])
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    r = pd.detect(doc)

    # The header has change: method for phone number no longer uses context
    exp = {
        "date": "2045-01-30",
        "format": "piisa:pii-collection:v1",
        "lang": "en",
        "stage": "detection",
        "detectors": {
            1: {
                "name": "regex for PHONE_NUMBER:international phone number",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1",
                "method": "regex"  # no context
            },
            2: {
                "name": "standard credit card",
                "source": "piisa:pii-extract-base:test",
                "version": "0.0.1",
                "method": "regex,checksum"
            }
        }
    }
    assert exp == r.header()


    pii = list(r)

    # Now, since we have deactivated context for phone numbers, there's one more
    assert len(pii) == 3

    exp = {
        'detector': 1,
        'type': 'PHONE_NUMBER',
        'subtype': 'international phone number',
        'process': {
            'stage': 'detection'
        },
        'value': '+34983453999',
        'chunkid': '3',
        'country': 'any',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 44,
        'end': 56
    }
    assert exp == pii[0].asdict()

    exp = {
        'detector': 2,
        'process': {
            'stage': 'detection'
        },
        'type': 'CREDIT_CARD',
        'value': '4273 9666 4581 5642',
        'chunkid': '4',
        'subtype': 'standard credit card',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 25,
        'end': 44
    }
    assert exp == pii[1].asdict()

    exp = {
        'detector': 1,
        'type': 'PHONE_NUMBER',
        'subtype': 'international phone number',
        'process': {
            'stage': 'detection'
        },
        'value': '+34983453000',
        'chunkid': '5',
        'country': 'any',
        'lang': 'en',
        'docid': '00000-11111',
        'start': 37,
        'end': 49
    }
    assert exp == pii[2].asdict()



def test300_tasks_detect_chunk(fixture_timestamp):
    """
    Test running a detection on a chunk
    """
    SRC = """My current credit card number is 4273 9666 4581 5642 and my phone
      number is +34983453999. This other one, however, is not a valid credit
      card number: 9999 9666 4581 5643"""
    chunk = DocumentChunk(id=0, data=SRC)

    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks(lang="en")

    piic = mod.PiiCollectionBuilder(lang="en")
    n = pd.detect_chunk(chunk, piic)
    assert n == 2

    exp = [
        {
            'detector': 1,
            'process': {
                'stage': 'detection'
            },
            'type': 'CREDIT_CARD',
            'subtype': 'standard credit card',
            'value': '4273 9666 4581 5642',
            'chunkid': '0',
            'lang': 'en',
            'start': 33,
            'end': 52
        },
        {
            'detector': 2,
            'process': {
                'stage': 'detection'
            },
            'type': 'PHONE_NUMBER',
            'subtype': 'international phone number',
            'value': '+34983453999',
            'chunkid': '0',
            'lang': 'en',
            'country': 'any',
            'start': 82,
            'end': 94
        }
    ]

    got = [p.asdict() for p in piic]
    assert exp == got


def test310_tasks_detect_chunk_multi(fixture_timestamp):
    """
    Test running a detection on a chunk, multilang
    """
    exp = [
        {
            'detector': 1,
            'process': {
                'stage': 'detection'
            },
            'type': 'CREDIT_CARD',
            'subtype': 'standard credit card',
            'value': '4273 9666 4581 5642',
            'chunkid': '0',
            'lang': 'any',
            'start': 33,
            'end': 52
        },
        {
            'detector': 2,
            'process': {
                'stage': 'detection'
            },
            'type': 'PHONE_NUMBER',
            'subtype': 'international phone number',
            'value': '+34983453999',
            'chunkid': '0',
            'lang': 'en',
            'country': 'any',
            'start': 82,
            'end': 94
        }
    ]

    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)

    SRC = """My current credit card number is 4273 9666 4581 5642 and my phone
      number is +34983453999. This other one, however, is not a valid credit
      card number: 9999 9666 4581 5643"""

    # Build for EN
    pd.build_tasks(lang="en")

    # Detect in an EN chunk
    chunk = DocumentChunk(id=0, data=SRC, context={"lang": "en"})
    piic = mod.PiiCollectionBuilder()
    n = pd.detect_chunk(chunk, piic)
    assert n == 2
    got = [p.asdict() for p in piic]
    assert exp == got

    # Detect in an ES chunk -- no tasks found, hence nothing detected
    chunk = DocumentChunk(id=0, data=SRC, context={"lang": "es"})
    piic = mod.PiiCollectionBuilder()
    n = pd.detect_chunk(chunk, piic)
    assert n == 0

    # Build for ES
    pd.build_tasks(lang="es")

    # Now detect again in an ES chunk -- this time we do get results
    n = pd.detect_chunk(chunk, piic)
    assert n == 1
    got = [p.asdict() for p in piic]
    assert exp[:1] == got


def test400_tasks_stats(fixture_timestamp):
    """
    Test fetching stats
    """

    config = load_config(CONFIGFILE)
    pd = mod.PiiProcessor(skip_plugins=True, config=config)
    pd.build_tasks("en")

    doc = LocalSrcDocumentFile(DOCUMENT)
    pd.detect(doc)

    stats = pd.get_stats()
    assert stats == {'num': {'calls': 1, 'entities': 2},
                     'entities': {'PHONE_NUMBER': 1, 'CREDIT_CARD': 1}}
