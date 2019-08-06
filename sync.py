from fs.memoryfs import MemoryFS
from fs.path import join, splitext, split, normpath, frombase
from utils import rename, editDistance
from utils import parse_serie_guessit as parse
from utils import rename as parse2
from utils import INFORMATION, WARNING, DEBUG, ERROR
from utils import temp_format, subs_formats, temp_gap
from utils import video_formats
from parser_serie import transform
from fs.wrap import read_only, cache_directory
from fs.errors import RemoteConnectionError, IllegalBackReference
from fs.errors import DirectoryExpected
import fs
import re
from copier import Copier

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

def points(name):
    if re.search('anime|managa',name,re.I) :
        return 0
    if re.search('trasmi|transmi|tx',name,re.I):
        return 1
    return 2


def skey(a):
    if re.search('anime|manga',a.name,re.I):
        return 0
    else:
        return 1

class BaseManager:

    def __init__(self, filesystem, logger=None):
        self.filesystem = cache_directory(read_only(filesystem))
        self.filesystem.desc('/')
        self.caps_list = {}
        self.results = []
        self.logger = logger
        self.copier = Copier(num_workers=None)
        self.copier.start()

    def close(self):
        self.filesystem.close()
        self.copier.stop()

    def list_dir(self, top):
        return [i.name for i in self.filesystem.scandir(top) if i.is_dir]

    def download(self, src_pth, src_file , dest_pth, dest_file, call=None):

        ff = fs.open_fs(dest_pth)
        self.copier.copy(self.filesystem, join(src_pth, src_file),
                        ff, join('/', dest_file),
                        call, inject_fs=True)

    def find_nexts(self, top='/', deep=0, maxdeep=2):
        if deep==0:
            self.results = []
        # print(top)
        if deep > maxdeep:
            return
        #if self.logger:
        #    self.logger.emit(top, INFORMATION)
        dirs, nondirs = [], []
        for name in self.filesystem.scandir(top):
            if name.is_dir:
                dirs.append(name)
            elif splitext(name.name)[1].lower() in video_formats:
                nondirs.append(name)
        # print(dirs,nondirs)
        for fil in nondirs:
            pp = rename(fil.name)
            t1 = ''
            t2 = 0
            try:
                if pp.is_video:
                    if pp.episode:
                        t1 = transform(pp.title)
                        fill = t1
                        if pp.season:
                            fill+= ' - '+str(pp.season)+'x'+str(pp.episode)
                        else:
                            fill+= ' - '+str(pp.episode)
                        fill+=pp.ext
                    else:
                        continue
                    t2 = pp.episode
                else:
                    continue
            except KeyError:
                if self.logger:
                    self.logger.emit("Error procesando: "+i, WARNING)
                continue
            bedd = 100
            gap=2
            near = ''
            for j in self.caps_list.keys():
                edd = editDistance(t1, j, True)
                if edd <= gap and edd < bedd:
                    near = j
                    bedd = edd
                    if edd == 0:
                        break
            if near != '':
                if isinstance(t2, str):
                    if 'x' in t2:
                        t2 = t2.split('x')[1]
                    if int(t2)>self.caps_list[near]:
                        best = (near, fil.name, top, fill)
                        self.results.append(best)
                        if self.logger:
                            self.logger.emit('Encontrado: '+str(best), INFORMATION)

        for name in sorted(dirs,key=skey):
            path = join(top, name.name)
            if not self.filesystem.islink(path):
                self.find_nexts(path, deep+1, maxdeep)

    def last(self, base):
        with read_only(fs.open_fs(base)) as ff:
            proces = []
            folds = []
            for i in ff.scandir('/'):
                if i.is_dir:
                    folds.append(i)
            for i in folds:
                path = join('/', i.name)
                try:
                    for j in ff.scandir(path):
                        if j.is_file and splitext(j.name)[1].lower() in video_formats:
                            proces.append((j, i))
                except (PermissionError, DirectoryExpected) as e:
                    self.logger.emit("Acceso denegado a"+join(base,i.name), ERROR)

            folds = {}
            for filee, fold in proces:
                fold = fold.name
                filee = filee.name
                try:
                    pp = parse(filee)
                    if pp.episode and not isinstance(pp.episode, str) and not isinstance(pp.episode, int):
                        pp = parse2(filee)
                except Exception as e:
                    self.logger.emit("Error procesando: "+join(base,fold,filee), WARNING)
                    self.logger.emit(str(e), ERROR)
                    continue
                t1 = transform(pp.title)
                fill = t1
                if pp.episode:
                    if pp.season:
                        fill+= ' - '+str(pp.season)+'x'+str(pp.episode)
                    else:
                        fill+= ' - '+str(pp.episode)
                    fill+=pp.ext
                else:
                    continue
                t2 = pp.episode

                if t1 in folds:
                    if folds[t1] < int(t2):
                        folds[t1]=int(t2)
                else:
                    folds[t1] = int(t2)
            self.caps_list = folds

    def find_nexts2(self, top='/', deep=0, maxdeep=2):
        if deep==0:
            self.results = []
        # print(top)
        if deep > maxdeep:
            return
        #if self.logger:
        #    self.logger.emit(top, INFORMATION)
        dirs, nondirs = [], []
        for name in self.filesystem.scandir(top):
            if name.is_dir:
                dirs.append(name)
            elif splitext(name.name)[1].lower() in video_formats:
                nondirs.append(name)
        # print(dirs,nondirs)
        for fil in nondirs:
            pp = rename(fil.name)
            t1 = ''
            t2 = 0
            try:
                if pp.is_video:
                    if pp.episode:
                        t1 = transform(pp.title)
                        fill = t1
                        if pp.season:
                            fill+= ' - '+str(pp.season)+'x'+str(pp.episode)
                        else:
                            fill+= ' - '+str(pp.episode)
                        fill+=pp.ext
                    else:
                        continue
                    t2 = pp.episode
                else:
                    continue
            except KeyError:
                if self.logger:
                    self.logger.emit("Error procesando: "+i, WARNING)
                continue
            bedd = 100
            gap=2
            near = ''
            for j in self.caps_list.keys():
                edd = editDistance(t1, j, True)
                if edd <= gap and edd < bedd:
                    near = j
                    bedd = edd
                    if edd == 0:
                        break
            if near != '':
                if isinstance(t2, str):
                    if 'x' in t2:
                        t2 = t2.split('x')[1]
                    if not(int(t2) in self.caps_list[near]):
                        best = (near, fil.name, top, fill)
                        self.results.append(best)
                        if self.logger:
                            self.logger.emit('Encontrado: '+str(best), INFORMATION)

        for name in sorted(dirs,key=skey):
            path = join(top, name.name)
            if not self.filesystem.islink(path):
                self.find_nexts2(path, deep+1, maxdeep)

    def last2(self, base):
        with read_only(fs.open_fs(base)) as ff:
            proces = []
            folds = []
            for i in ff.scandir('/'):
                if i.is_dir:
                    folds.append(i)
            for i in folds:
                path = join('/', i.name)
                try:
                    for j in ff.scandir(path):
                        if j.is_file and splitext(j.name)[1].lower() in video_formats:
                            proces.append((j, i))
                except (PermissionError, DirectoryExpected) as e:
                    self.logger.emit("Acceso denegado a"+join(base,i.name), ERROR)

            folds = {}
            for filee, fold in proces:
                fold = fold.name
                filee = filee.name
                try:
                    pp = parse(filee)
                    if pp.episode and not isinstance(pp.episode, str) and not isinstance(pp.episode, int):
                        pp = parse2(filee)
                except Exception as e:
                    self.logger.emit("Error procesando: "+join(base,fold,filee), WARNING)
                    self.logger.emit(str(e), ERROR)
                    continue
                t1 = transform(pp.title)
                fill = t1
                if pp.episode:
                    if pp.season:
                        fill+= ' - '+str(pp.season)+'x'+str(pp.episode)
                    else:
                        fill+= ' - '+str(pp.episode)
                    fill+=pp.ext
                else:
                    continue
                t2 = pp.episode

                if t1 in folds:
                    folds[t1].add(int(t2))
                else:
                    folds[t1] = set()
                    folds[t1].add(int(t2))
            self.caps_list = folds

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.filesystem.close()
        self.copier.stop()
        return False