import re
import os
from parser_serie import rename_serie

INFORMATION = 0
WARNING = 1
ERROR = 2
DEBUG = 3

LOG_COLORS = {INFORMATION: "green", WARNING: "orange", ERROR: "red",
              DEBUG: "blue"}


def logcolor(txt, level):
    return "<font color=\""+LOG_COLORS[level]+"\">"+txt+"</font>"


def logsize(txt, size):
    return "<h"+str(size)+">"+txt+"</h"+str(size)+">"


stopwords = set(['no', 'wa', 'the', 'ga', 'san', 'to', 'ni','wo'])


def transform(txt):
    res = []
    for i in txt.split():
        if i.lower() in stopwords:
            res.append(i.lower())
        elif i == " ":
            continue
        elif len(i) == 1:
            res.append(i)
        else:
            res.append(i[0].upper()+i[1:].lower())
    return ' '.join(res)


def editDistance(a, b, transf=True):
        """Distancia de Leventein entre dos cadenas de texto.
            a,b son string
            devuelve un int
        """
        if transf:
            a = transform(a)
            b = transform(b)
        else:
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
                        m[i-1][j-1]+1, (min(m[i][j-1]+1, m[i-1][j]+1)))
        ret = m[len(b)][len(a)]
        return ret


eb = re.compile('\{.+\}|\(.+\)|\[.+\]')
epi = re.compile('[Ee]pisodio|[Cc]ap[ií]tulo')
split = re.compile('([0-9]+[xX]?[0-9]*) *-? *')
normsp = re.compile('  +')
endesp = re.compile(' +$')
begesp = re.compile('^ +')
formats = {'.mp4': 0, '.mkv': 0, '.avi': 0, '.rm': 0, '.rmv': 0,'.str': 0}

def rename(name):
    err = False
    txt, ext = os.path.splitext(name)
    try:
        t1, t2 = rename_serie(txt)
    except (ValueError, IndexError):
        return '', '', '', True
    return t1, t2, ext, err

formatt=re.compile(' *- *([0-9]+)')
