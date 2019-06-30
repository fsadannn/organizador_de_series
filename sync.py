from fs.memoryfs import MemoryFS
from fs.path import join, splitext, split
from utils import rename, editDistance
from utils import temp_format, subs_formats, temp_gap
from parser_serie import transform
from fs.wrap import read_only, cache_directory
import fs

def best_ed(name, sett, gap=2):
    near = ''
    bedd = 100
    for j in sett:
        edd = editDistance(name, j, True)
        if edd <= gap and edd < bedd:
            near = j
            bedd = edd
            if edd == 0:
                break
    if near == '':
        return name
    return near

def make_temp_fs(fff):
        # make virtual filesystem in ram with the final
        # organization of the filesystem
        ff = cache_directory(read_only(fff))
        ram = MemoryFS()

        # for path, dirs, files in ff.walk():
        posprocsub = []
        fils = set()
        files = ff.scandir('/')
        path = '/'
        folds = set([ i.name for i in files if i.is_dir])
        files = ff.scandir('/')
        for j in files:
            if not j.is_file:
                continue
            if splitext(j.name)[1] in subs_formats:
                posprocsub.append(j.name)
                continue
            pp = rename(j.name)
            try:
                if pp.is_video:
                    fold = transform(pp.title)
                    if not(fold in folds):
                        fold = best_ed(fold, folds)
                        folds.add(fold)
                    pth = join('/',fold)
                    if not ram.exists(pth):
                        ram.makedir(fold)
                    fils.add(fold)
                    if pp.episode:
                        fill = fold+' - '+str(pp.episode)
                    else:
                        fill = fold
                    if pp.episode_title:
                        fill = fill+' - '+str(pp.episode_title)
                    fill += pp.ext
                    ram.writetext(join(pth,fill),join(path,j.name))
            except KeyError:
                continue

            for j in posprocsub:
                pp = rename(j)
                fold = transform(pp.title)
                pth = join('/',fold)
                if pp.episode:
                    fill = fold+' - '+str(pp.episode)
                else:
                    fill = fold
                if pp.episode_title:
                    fill = fill+' - '+str(pp.episode_title)
                fill += pp.ext
                if ram.exists(pth):
                    ram.writetext(join(pth,fill),join(path,j))
                elif len(fils)==1:
                    pth = join('/',list(fils)[0])
                    ram.writetext(join(pth,fill),join(path,j))
                elif len(fils)>1:
                    best = None
                    gap = 3
                    for i in fils:
                        n = editDistance(i,foldd)
                        if n < 3 and n < gap:
                            best=i
                            gap=n
                        elif n == 0:
                            best = i
                            break
                    if best:
                        pth = join('/',best)
                        ram.writetext(join(pth,fill),join(path,j))
                    else:
                        if not(ram.exists('/subs')):
                            ram.makedir('/subs')
                        ram.writetext(join('/subs',j),join(path,j))
                else:
                    if not(ram.exists('/subs')):
                        ram.makedir('/subs')
                    ram.writetext(join('/subs',j),join(path,j))
        return ram
