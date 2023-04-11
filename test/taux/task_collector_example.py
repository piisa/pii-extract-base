
from pathlib import Path

from pii_extract.gather.collection.sources import FolderTaskCollector


class MyTestTaskCollector(FolderTaskCollector):

    def __init__(self, **kwargs):
        basedir = Path(__file__).parent / "modules"
        super().__init__("taux.modules", basedir, 'piisa:pii-extract-base:test',
                         version='0.0.1', debug=False, **kwargs)
