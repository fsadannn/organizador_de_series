from collections import defaultdict
from collections.abc import MutableMapping
from dataclasses import dataclass
from math import floor
from typing import Dict, Iterator, List, Set, Text, Union

from fs.base import FS
from fs.info import Info
from fs.memoryfs import MemoryFS
from fs.path import join, splitext
from fs.wrap import cache_directory, read_only

from .edit_distance import best_ed, editDistance
from .formats import get_ext, is_video, subs_formats
from .rename import ChapterMetadata
from .rename import rename as rename_serie


def to_int(n: Union[float, int]) -> Union[float, int]:
    if abs(n - floor(n)) < 1e-9:
        return int(n)

    return n


def make_temp_fs(fff: FS) -> FS:
    # make virtual filesystem in ram with the final
    # organization of the filesystem
    ff: FS = cache_directory(read_only(fff))
    ram: FS = MemoryFS()

    # for path, dirs, files in ff.walk():
    posprocsub: List[str] = []
    new_files: Set[Text] = set()

    files: Iterator[Info] = ff.scandir('/')

    path: str = '/'
    folders: Set[Text] = set([i.name for i in files if i.is_dir])

    files: Iterator[Info] = ff.scandir('/')

    for k in files:
        if not k.is_file:
            continue

        if splitext(k.name)[1].lower() in subs_formats:
            posprocsub.append(k.name)
            continue

        serie: ChapterMetadata = rename_serie(k.name)

        try:
            if is_video(k.name):
                folder = serie.serie_name

                if not(folder in folders):
                    folder = best_ed(folder, folders, 2)
                    folders.add(folder)

                pth = join('/', folder)

                ram.makedir(folder, recreate=True)

                new_files.add(serie.serie_name)

                if serie.episode:
                    if serie.season:
                        file_name = f'{serie.serie_name} - {serie.season_number()}X{serie.episode_number()}'
                    else:
                        file_name = f'{serie.serie_name} - {serie.episode_number()}'
                else:
                    file_name = serie.serie_name

                if serie.chapter_name:
                    file_name = f'{file_name} - {serie.chapter_name}'

                file_name += get_ext(k.name)

                ram.settext(join(pth, file_name), join(path, k.name))
        except KeyError:
            continue

    for j in posprocsub:
        serie: ChapterMetadata = rename_serie(j)

        folder = serie.serie_name
        pth = join('/', folder)

        if serie.episode:
            if serie.season:
                file_name = f'{serie.serie_name} - {serie.season_number()}X{serie.episode_number()}'
            else:
                file_name = f'{serie.serie_name} - {serie.episode_number()}'
        else:
            file_name = serie.serie_name

        if serie.chapter_name:
            file_name = f'{file_name} - {serie.chapter_name}'

        file_name += get_ext(j)

        if ram.exists(pth):
            ram.settext(join(pth, file_name), join(path, j))

        elif len(new_files) == 1:
            pth = join('/', list(new_files)[0])
            ram.settext(join(pth, file_name), join(path, j))

        elif len(new_files) > 1:
            best = None
            gap = 3

            for i in new_files:
                n = editDistance(i, folder)

                if n < 3 and n < gap:
                    best = i
                    gap = n
                elif n == 0:
                    best = i
                    break

            if best:
                pth = join('/', best)
                ram.settext(join(pth, file_name), join(path, j))
            else:
                ram.makedir('/subs', recreate=True)
                ram.settext(join('/subs', j), join(path, j))
        else:
            ram.makedir('/subs', recreate=True)
            ram.settext(join('/subs', j), join(path, j))

    return ram


@dataclass
class ChaptersRange:
    being: int
    end: int

    @property
    def gap(self) -> int:
        return self.end - self.being

    def as_text(self) -> str:
        if self.gap == 2:
            return f'{self.being+1}'

        return f'{self.being+1}-{self.end-1}'


class SerieFolder(MutableMapping):
    __slots__ = ('_series', 'name')

    def __init__(self, name: str) -> None:
        self._series: Dict[str, Set[Union[float, int]]] = defaultdict(set)
        self.name = name

    def __contains__(self, x: str):
        return x in self._series

    def __len__(self):
        return len(self._series)

    def __iter__(self):
        for i in self._series:
            yield i

    def __getitem__(self, key: str) -> Set[Union[int, float]]:
        return self._series[key]

    def __setitem__(self, key: str, value: Union[int, float]):
        self._series[key].add(value)

    def __delitem__(self, key):
        del self._series[key]

    def last(self, key: str) -> Union[int, float]:
        return max(self._series[key])

    def compute_lost_chapters(self, key: str) -> List[ChaptersRange]:
        current: int = 0
        lost_chapters: List[ChaptersRange] = []

        for i in sorted(self._series[key]):
            if i - current <= 1:
                current = i
                continue

            lost_chapters.append(ChaptersRange(being=current, end=i))
            current = i

        return lost_chapters


class SerieFS(MutableMapping):
    __slots__ = ('_fs',)

    def __init__(self) -> None:
        self._fs: Dict[str, SerieFolder] = {}

    def __contains__(self, x: str):
        return x in self._fs

    def __len__(self):
        return len(self._fs)

    def __iter__(self):
        for i in self._fs:
            yield i

    def __getitem__(self, key: str) -> SerieFolder:
        return self._fs[key]

    def __setitem__(self, key: str, value: Union[str, SerieFolder]):
        if isinstance(value, SerieFolder):
            self._fs[key] = value
        else:
            self._fs[key] = SerieFolder(value)

    def __delitem__(self, key):
        del self._fs[key]

    def add_serie_episode(self, folder_name: str, serie_name: str, episode: Union[int, float]):
        episode = to_int(episode)

        if folder_name in self:
            if serie_name in self[folder_name]:
                self[folder_name][serie_name] = episode
                return

            name = best_ed(serie_name, self[folder_name].keys(), 2)
            self[folder_name][name] = episode

        self[folder_name] = serie_name
        self[folder_name][serie_name] = episode
