import os
from dataclasses import dataclass

from ..series_renamer import ChapterMetadata, Processor


@dataclass
class ChapterMap:
    fixname: str
    chapter: int
    season: int
    original: str
    ext: str
    vpath: str
    state: bool
    fold: str


def rename(name: str) -> ChapterMetadata:
    txt, ext = os.path.splitext(name)
    ext = ext.lower()

    data: ChapterMetadata = Processor()(txt)

    return data
