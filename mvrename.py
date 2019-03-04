
import sys
import os
import shutil as sh
from threading import Thread
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QWidget, QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtWidgets import QListWidget, QButtonGroup, QRadioButton
from PyQt5.QtCore import Qt, pyqtSignal
from utils import INFORMATION, WARNING, DEBUG, ERROR, formats
from utils import rename, editDistance


class MoveRename(QWidget):

    loggin = pyqtSignal(str, int)

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
        tt3 = QRadioButton("Renombrar a #")
        self.move.addButton(tt1, 1)
        self.move.addButton(tt2, 2)
        self.move.addButton(tt3, 3)
        self.move.setExclusive(True)
        tt.addWidget(self.all)
        tt.addWidget(self.invert)
        tt.addStretch()
        tt.addWidget(tt1)
        tt.addWidget(tt2)
        tt.addWidget(tt3)
        self.cl.addLayout(tt)

        self.li = QListWidget()
        self.cl.addWidget(self.li)
        self.li.itemDoubleClicked.connect(self.edititem)

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
        self.move.buttonClicked.connect(self.gen_list)
        self.movethread = None

    def gen_list(self, id):
        if self.pathbar.text() == '':
            return
        self.build_ui_caps()

    def procces(self):
        if self.pathbar.text() == '':
            return
        if self.move.checkedId() == 1:
            self.movef(self.pathbar.text())
        else:
            self.renamef(self.pathbar.text())

    def edititem(self, item):
        cps = self.caps
        cpsm = self.capsmap
        txt = item.text().split("\t")
        text, ok = QInputDialog.getText(None, "Editar",
                                        "Nombre:", QLineEdit.Normal,
                                        txt[0])
        if ok and text!='' and not text is None:
            cps[cpsm[txt[1]]]['fixname'] = text
            item.setText(text+'\t'+txt[1])
            item.setCheckState(Qt.Checked)

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
        nonly = self.move.checkedId() == 3
        li = self.li
        lic = li.count()
        cpl = len(self.caps)
        cps = self.caps
        if cpl <= lic:
            for n, i in enumerate(cps):
                name = i['fixname']
                if nonly:
                    t1, t2, ext, err = rename(name)
                    name = t2+ext
                ll = li.item(n)
                ll.setText(name+"\t"+i['original'])
            for i in range(lic-cpl):
                ll = li.takeItem(0)
                del ll
        else:
            for i in range(lic):
                name = cps[i]['fixname']
                if nonly:
                    t1, t2, ext, err = rename(name)
                    name = t2+ext
                ll = li.item(i)
                ll.setText(name+"\t"+cps[i]['original'])
            for i in range(cpl-lic):
                name = cps[lic+i]['fixname']
                if nonly:
                    t1, t2, ext, err = rename(name)
                    name = t2+ext
                li.addItem(name+"\t"+cps[lic+i]['original'])

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
            t1, t2, ext, err = rename(i)
            if err:
                self.loggin.emit("Error procesando: "+i, WARNING)
                continue
            folders.append(t1)
            # printprint(t1,type(t1),t2,type(t2))
            if str(t2):
                strt = t1+' - '+str(t2)+ext
            else:
                strt = t1+ext
            caps.append({'original':i, 'fixname':strt, 'folder':t1})
            capsmap[i] = len(caps)-1

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
                return
        self.movethread = Thread(target=self._movef, args=(path,))
        self.movethread.start()

    def renamef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
                return
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
                txt = item.text().split("\t")[1]
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
            self.loggin.emit("Moviendo: "+i['original']+' para '+i['folder'], INFORMATION)
            sh.copy2(os.path.join(path,i['original']),os.path.join(path,i['folder'],i['fixname']))
            os.remove(os.path.join(path,i['original']))
        self.loggin.emit("Mover finalizado.", DEBUG)
        self.sort_cap(path)
        self.build_ui_caps()

    def _renamef(self, path):
        nonly = self.move.checkedId()==3
        li = self.li
        cps = self.caps
        cpsm = self.capsmap
        caps = []
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == 2:
                txt = item.text().split("\t")[1]
                caps.append(cps[cpsm[txt]])

        temp = set()
        for i in caps:
            name = i['fixname']
            if nonly:
                t1, t2, ext, err = rename(name)
                name = t2+ext
            if name in temp:
                os.remove(os.path.join(path, i['original']))
                self.loggin.emit('Remove', ERROR)
                continue
            try:
                self.loggin.emit("Renombrando: "+i['original']+'  a  '+name, INFORMATION)
                os.renames(os.path.join(path,i['original']),os.path.join(path,name))
                temp.add(name)
            except Exception as e:
                self.loggin.emit(str(e), ERROR)
        self.loggin.emit("Renombrar finalizado.", DEBUG)
        self.sort_cap(path)
        self.build_ui_caps()
