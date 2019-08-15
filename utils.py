import re
import os
import sys
import json
from guessit import guessit
from parser_serie import rename_serie
from PyQt5.QtCore import QObject

class Logger(QObject):
    __slots__ = ('__name', '__signal')
    def __init__(self, name, signal):
        self.__name = name
        self.__signal = signal

    def emit(self, txt, num):
        self.__signal.emit(self.__name, txt, num)

    @property
    def signal(self):
        return self.__signal

def reconnect(signal, newhandler=None, oldhandler=None):
    while True:
        try:
            if oldhandler is not None:
                signal.disconnect(oldhandler)
            else:
                signal.disconnect()
        except TypeError:
            break
    if newhandler is not None:
        signal.connect(newhandler)

if hasattr(sys, 'frozen'):
    MODULE = os.path.dirname(sys.executable)
else:
    try:
        MODULE = os.path.dirname(os.path.realpath(__file__))
    except:
        MODULE = ""

INFORMATION = 0
WARNING = 1
ERROR = 2
DEBUG = 3
NAME = 4

LOG_COLORS = {INFORMATION: "green", WARNING: "orange", ERROR: "red",
              DEBUG: "blue", NAME: "yellow"}


def logcolor(txt, level):
    return "<font color=\""+LOG_COLORS[level]+"\">"+txt+"</font>"


def logsize(txt, size):
    return "<h"+str(size)+">"+txt+"</h"+str(size)+">"


class CapData:
    def __init__(self, name, nameep, num, ext, informats, err, season=None, mimetype=None):
        self._things = {'title': name, 'episode_title': nameep, 'episode': num,
                        'ext': ext, 'is_video': informats, 'error': err,
                        'mimetype': mimetype, 'season': season}
        self._map = {0: name, 1: num, 2: ext, 3: informats, 4: nameep, 5: err}

    def __getattr__(self, name):
        classname = self.__class__.__name__
        if name in self._things:
            return self._things[name]
        raise AttributeError("\'{classname}\' object has no attribute \'{name}\'".format(**locals()))

    def __getitem__(self, item):
        if item in self._things:
            return self._things[item]
        if item in self._map:
            return self._map[item]
        raise KeyError(str(self.__class__.__name__)+" don\'t have key "+str(item))

    def __str__(self):
        return str(self._things)

subs_formats = set([".srt",".idx",".sub",".ssa",".ass"])
video_formats = set([".3g2",
                ".3gp",
                ".3gp2",
                ".asf",
                ".avi",
                ".divx",
                ".flv",
                ".mk3d",
                ".m4v",
                ".mk2",
                ".mka",
                ".mkv",
                ".mov",
                ".mp4",
                ".mp4a",
                ".mpeg",
                ".mpg",
                ".ogg",
                ".ogm",
                ".ogv",
                ".ra",
                ".ram",
                ".rm",
                ".ts",
                ".wav",
                ".webm",
                ".wma",
                ".wmv",
                ".vob"])


def editDistance(a, b, lower=False):
        """Distancia de Leventein entre dos cadenas de texto.
            a,b son string
            devuelve un int
        """
        if lower:
            a = a.lower()
            b = b.lower()
        m = []
        m.append([i for i in range(len(a)+1)])
        for i in range(len(b)):
            m.append([i+1]+[0 for i in range(len(a))])
        for i in range(1, len(b)+1):
            for j in range(1, len(a)+1):
                if a[j-1] == b[i-1]:
                    m[i][j] = m[i-1][j-1]
                else:
                    m[i][j] = min(
                        m[i-1][j-1]+1, min(m[i][j-1]+1, m[i-1][j]+1))
        ret = m[len(b)][len(a)]
        return ret


def parse_serie_guessit(title, params=None):
    if not params:
        params = '--json --no-default-config -E -t episode -c \"'+os.path.join(MODULE,'options.json\"')
    txt, ext = os.path.splitext(title)
    ext = ext.lower()
    a = guessit(title, params)
    titlee = a['title']
    ept = ''
    try:
        ept = a['episode_title']
    except:
        pass
    ep = ''
    try:
        ep = a['episode']
    except:
        pass
    mime = None
    try:
        mime = a['mimetype']
    except:
        pass
    ss = None
    try:
        ss = a['season']
    except:
        pass
    dd = CapData(titlee, ept, ep, ext,  bool(ext in video_formats),
            False, ss, mime)
    return dd


def rename(name):
    err = False
    txt, ext = os.path.splitext(name)
    ext = ext.lower()
    try:
        t1, t2, t3 = rename_serie(txt)
    except (ValueError, IndexError):
        try:
            rr = parse_serie_guessit(name)
            ep = ''
            if 'episode' in rr:
                if isinstance(rr['episode'], list) or isinstance(rr['episode'],tuple):
                    ep = rr['episode'][-1]
                else:
                    ep = rr['episode']
            ept = ''
            if 'episode_title' in rr:
                ept = rr['episode_title']
            return CapData(rr['title'], ept, ep, ext, bool(ext in video_formats), err)
        except:
            return CapData(txt, '', '', ext, bool(ext in video_formats), True)
    data = {''}
    return CapData(t1, t3, t2, ext, bool(ext in video_formats), err)


def temp_format(ss):
    return '[Temp '+str(ss)+']'

temp_gap = len(temp_format('10'))