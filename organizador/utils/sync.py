from typing import Iterator, List, Set, Text

from fs.base import FS
from fs.info import Info
from fs.memoryfs import MemoryFS
from fs.path import join, splitext
from fs.wrap import cache_directory, read_only

from .edit_distance import best_ed, editDistance
from .formats import get_ext, is_video, subs_formats
from .rename import ChapterMetadata
from .rename import rename as rename_serie


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

    for j in files:
        if not j.is_file:
            continue

        if splitext(j.name)[1] in subs_formats:
            posprocsub.append(j.name)
            continue

        serie: ChapterMetadata = rename_serie(j.name)

        try:
            if is_video(j.name):
                folder = serie.serie_name

                if not(folder in folders):
                    folder = best_ed(folder, folders)
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

                file_name += get_ext(j.name)

                ram.settext(join(pth, file_name), join(path, j.name))
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
                file_name += f'{file_name} - {serie.chapter_name}'

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
