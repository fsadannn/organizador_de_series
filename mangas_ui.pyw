# -*- coding: UTF-8 -*-
#!/usr/bin python3
# @author: SadanNN
# mover para un hilo el mover ficheros

import sys
import os
import re
import shutil as sh
from threading import Thread
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QWidget, QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtWidgets import QListWidget, QButtonGroup, QRadioButton
from PyQt5.QtWidgets import QTextEdit, QDockWidget
from PyQt5.QtCore import Qt, pyqtSignal
try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

INFORMATION = 0
WARNING = 1
ERROR = 2
DEBUG = 3

LOG_COLORS = {INFORMATION: "green", WARNING: "yellow", ERROR: "red",
              DEBUG: "blue"}

def logcolor(txt, level):
    return "<font color=\""+LOG_COLORS[level]+"\">"+txt+"</font>"

def logsize(txt, size):
    return "<h"+str(size)+">"+txt+"</h"+str(size)+">"

stopwords = set(['no','wa','the','ga','san','to','ni'])


def transform(txt):
    res = []
    for i in txt.split():
        if i in stopwords:
            res.append(i)
        elif i == " ":
            continue
        elif len(i) == 1:
            res.append(i)
        else:
            res.append(i[0].upper()+i[1:].lower())
    return ' '.join(res)

def editDistance(a, b, transf = True):
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
        for i in range(1,len(b)+1):
            for j in range(1,len(a)+1):
                if a[j-1] == b[i-1]:
                    m[i][j] = m[i-1][j-1]
                else:
                    m[i][j] = min(m[i-1][j-1]+1, (min(m[i][j-1]+1, m[i-1][j]+1)))
        ret = m[len(b)][len(a)]
        return ret

eb = re.compile('\{.+\}|\(.+\)|\[.+\]')
epi = re.compile('[Ee]pisodio|[Cc]ap[ií]tulo')
split = re.compile('([0-9]+[xX]?[0-9]*) *-? *')
normsp = re.compile('  +')
endesp = re.compile(' +$')
begesp = re.compile('^ +')
formats = {'.mp4':0,'.mkv':0,'.avi':0,'.rm':0,'.rmv':0}


class MoveRename(QWidget):

    loggin = pyqtSignal(str,int)
    def __init__(self):
        super(MoveRename, self).__init__()
        self.cl = QVBoxLayout()

        tt = QHBoxLayout()
        self.pathbar = QLineEdit()
        self.pathbtn = QPushButton("Cambiar")
        tt.addWidget(self.pathbar)
        tt.addWidget(self.pathbtn)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.all = QPushButton("Todo")
        self.invert = QPushButton("Invertir")
        self.move = QButtonGroup()
        tt1 = QRadioButton("Mover")
        tt1.setChecked(True)
        tt2 = QRadioButton("Renombrar")
        self.move.addButton(tt1, 1)
        self.move.addButton(tt2, 2)
        self.move.setExclusive(True)
        tt.addWidget(self.all)
        tt.addWidget(self.invert)
        tt.addStretch()
        tt.addWidget(tt1)
        tt.addWidget(tt2)
        self.cl.addLayout(tt)

        self.li = QListWidget()
        self.cl.addWidget(self.li)

        tt = QHBoxLayout()
        self.proc = QPushButton("Procesar")
        tt.addWidget(self.proc)
        tt.addStretch()
        self.cl.addLayout(tt)

        self.setLayout(self.cl)

        self.pathbtn.clicked.connect(self.set_path)
        self.li.itemClicked.connect(self.check_item)
        self.all.clicked.connect(self.allf)
        self.invert.clicked.connect(self.invertf)
        self.proc.clicked.connect(self.procces)
        self.movethread = None

    def procces(self):
        if self.pathbar.text() == '':
            return
        if self.move.checkedId() == 1:
            self.movef(self.pathbar.text())
        else:
            self.renamef(self.pathbar.text())

    def allf(self):
        li = self.li
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)

    def invertf(self):
        li = self.li
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    def check_item(self, item):
        if item.checkState() == Qt.Unchecked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def set_path(self):
        dirr = self.get_path()
        if dirr is None or dirr == '':
            return
        self.pathbar.setText(dirr)
        self.sort_cap(dirr)
        self.build_ui_caps()
        self.allf()

    def build_ui_caps(self):
        li = self.li
        lic = li.count()
        cpl = len(self.caps)
        cps = self.caps
        if cpl <= lic:
            for n, i in enumerate(cps):
                ll = li.item(n)
                ll.setText(i['fixname']+"\t"+i['original'])
            for i in range(lic-cpl):
                ll = li.takeItem(0)
                del ll
        else:
            for i in range(lic):
                ll = li.item(i)
                ll.setText(cps[i]['fixname']+"\t"+cps[i]['original'])
            for i in range(cpl-lic):
                li.addItem(cps[lic+i]['fixname']+"\t"+cps[lic+i]['original'])

    def get_path(self):
        txt = self.pathbar.text()
        if txt is None or txt == "":
            txt = ""
        dirr = QFileDialog.getExistingDirectory(self, "Selecionar Directorio",
                                                 txt,
                                                 QFileDialog.ShowDirsOnly
                                                 | QFileDialog.DontResolveSymlinks)
        # print(dirr)
        return dirr

    def sort_cap(self, path):
        l = os.listdir(path)
        proces = []
        folds = []
        for i in l:
            if os.path.isfile(os.path.join(path, i)) and os.path.splitext(i)[1] in formats:
                proces.append(i)
            else:
                folds.append(i)

        folders = []
        caps = []
        capsmap = {}
        for i in proces:
            txt, ext = os.path.splitext(i)
            txt = eb.sub('', txt)
            txt = txt.replace('-', ' ')
            txt = epi.sub('-', txt)
            txt = normsp.sub(' ', txt)

            try:
                tt = ''.join(list(reversed(txt)))
                hh = list(reversed(list(map(lambda x:''.join(list(reversed(x))),
                            list(filter(lambda x:x!='' and x!=' ',split.split(tt,1)))))))
                t1, t2 = hh[0],hh[1]
                t1 = transform(t1)
            except (ValueError, IndexError):
                self.loggin.emit("Error procesando: "+i, WARNING)
                #print('Error procesing '+i)
                continue
            t1 = endesp.sub('', t1)
            t1 = begesp.sub('', t1)
            t2 = endesp.sub('', t2)
            t2 = begesp.sub('', t2)
            folders.append(t1)
            strt = t1+' - '+t2+ext
            caps.append({'original':i, 'fixname':strt, 'folder':t1})
            capsmap[strt] = len(caps)-1

        folders = list(set(folders))
        fnew = []
        remap = {}
        for i in folders:
            ver = True
            near = ''
            for j in folds:
                edd = editDistance(i, j, False)
                if edd <= 4:
                    ver = False
                    near = j
                    if edd == 0:
                        edd = editDistance(i, j)
                    break
            if ver:
                fnew.append(i)
            else:
                if edd != 0:
                    remap[i] = j

        self.fnew = set(fnew)
        self.remap = remap
        self.caps = caps
        self.capsmap = capsmap

    def movef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
        self.movethread = Thread(target=self._movef, args=(path,))
        self.movethread.start()

    def renamef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
        self.movethread = Thread(target=self._renamef, args=(path,))
        self.movethread.start()

    def _movef(self, path):
        li = self.li
        cps = self.caps
        cpsm = self.capsmap
        fn = self.fnew
        caps = []
        fnew = set()
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == 2:
                txt = item.text().split("\t")[0]
                caps.append(cps[cpsm[txt]])
                dd = caps[-1]['folder']
                if dd in fn:
                    fnew.add(dd)

        remap = self.remap
        for i in fnew:
            try:
                os.mkdir(os.path.join(path,i))
                self.loggin.emit("Creando carpeta: "+i, INFORMATION)
            except Exception as e:
                self.loggin.emit(str(e), ERROR)

        for i in caps:
            if i['folder'] in remap:
                i['folder'] = remap[i['folder']]
            sh.copy2(os.path.join(path,i['original']),os.path.join(path,i['folder'],i['fixname']))
            self.loggin.emit("Moviendo: "+i['original']+' para '+i['folder'], INFORMATION)
            os.remove(os.path.join(path,i['original']))
        self.loggin.emit("Mover finalizado.", DEBUG)
        self.sort_cap(path)
        self.build_ui_caps()

    def _renamef(self, path):
        li = self.li
        cps = self.caps
        cpsm = self.capsmap
        caps = []
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == 2:
                txt = item.text().split("\t")[0]
                caps.append(cps[cpsm[txt]])

        temp = set()
        for i in caps:
            if i['fixname'] in temp:
                os.remove(os.path.join(path, i['original']))
                self.loggin.emit('Remove', ERROR)
                continue
            try:
                os.renames(os.path.join(path,i['original']),os.path.join(path,i['fixname']))
                self.loggin.emit("Renombrando: "+i['original']+'  a  '+i['fixname'], INFORMATION)
                temp.add(i['fixname'])
            except Exception as e:
                self.loggin.emit(str(e), ERROR)
        self.loggin.emit("Renombrar finalizado.", DEBUG)
        self.sort_cap(path)
        self.build_ui_caps()


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        self.cw1 = MoveRename()
        self.setCentralWidget(self.cw1)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logsdock = QDockWidget("Logs", self)
        self.logsdock.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.logsdock.setWidget(self.logs)
        self.logsdock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logsdock)
        self.cw1.loggin.connect(self.loggin)

    def loggin(self, txt, level):
        if self.logs.document().lineCount()>1000:
            self.logs.clear()
        txt = logcolor(txt, level)
        self.logs.append(txt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w=Main()
    w.show()
    w.resize(784,521)
    sys.exit(app.exec_())
