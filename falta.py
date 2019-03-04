import sys
import os
import re
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtWidgets import QTreeWidget, QLineEdit, QButtonGroup
from PyQt5.QtWidgets import QTreeWidgetItem
from utils import INFORMATION, WARNING, DEBUG, ERROR, formats, formatt
from utils import rename, editDistance


fff = re.compile('')
def filt(t):
    pass
    # funcion para capitulos en el formato temp[xX]caps


class Falta(QWidget):

    loggin = pyqtSignal(str, int)

    def __init__(self):
        super(Falta, self).__init__()
        self.cl = QVBoxLayout()

        tt = QHBoxLayout()
        self.pathbar = QLineEdit()
        self.pathbtn = QPushButton("Cambiar")
        tt.addWidget(self.pathbar)
        tt.addWidget(self.pathbtn)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.move = QButtonGroup()
        tt1 = QRadioButton("Falta")
        tt1.setChecked(True)
        tt2 = QRadioButton("Último")
        self.move.addButton(tt1, 1)
        self.move.addButton(tt2, 2)
        self.move.setExclusive(True)
        tt.addWidget(tt1)
        tt.addWidget(tt2)
        tt.addStretch()
        self.cl.addLayout(tt)

        self.li = QTreeWidget()
        self.li.setColumnCount(1)
        self.cl.addWidget(self.li)

        tt = QHBoxLayout()
        self.proc = QPushButton("Buscar")
        tt.addWidget(self.proc)
        tt.addStretch()
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)

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

    def set_path(self):
        dirr = self.get_path()
        if dirr is None or dirr == '':
            return
        self.pathbar.setText(dirr)

    def procces(self):
        if self.pathbar.text() == '':
            return
        li = self.li
        li.clear()
        if self.move.checkedId() == 1:
            self.falta_caps()
            caps_list = self.caps_list
            for i in sorted(caps_list.keys()):
                parent = QTreeWidgetItem()
                parent.setText(0, i)
                addp = False
                for k in sorted(caps_list[i].keys()):
                    data = [0]+list(sorted(caps_list[i][k]))
                    for j in range(len(data)-1):
                        if data[j+1]-data[j] > 1:
                            if data[j+1]-data[j] == 2:
                                txt = k + " : " + str(data[j]+1)
                                addp = True
                            else:
                                txt = k + " : " + \
                                    str(data[j]+1) + '-' + str(data[j+1]-1)
                                addp = True
                            child = QTreeWidgetItem(parent)
                            child.setText(0, txt)
                            parent.addChild(child)
                #print(i, addp)
                if addp:
                    li.addTopLevelItem(parent)
                else:
                    del parent
        else:
            self.last()
            caps_list = self.caps_list
            for i in sorted(caps_list.keys()):
                parent = QTreeWidgetItem()
                parent.setText(0, i)
                for k in sorted(caps_list[i].keys()):
                    txt = k + " - " + str(caps_list[i][k])
                    child = QTreeWidgetItem(parent)
                    child.setText(0, txt)
                    parent.addChild(child)
                li.addTopLevelItem(parent)

    def last(self):
        base = self.pathbar.text()
        l = os.listdir(base)
        proces = []
        folds = []
        for i in l:
            path = os.path.join(base, i)
            if os.path.isdir(path):
                folds.append(i)
        for i in folds:
            path = os.path.join(base, i)
            try:
                t = os.listdir(path)
                for j in t:
                    if os.path.isfile(os.path.join(path, j)) and (os.path.splitext(j)[1] in formats):
                        proces.append((j, i))
            except PermissionError as e:
                self.loggin.emit("Acceso denegado a"+i, ERROR)

        folds = {}
        for filee, fold in proces:
            # print(fold, filee)
            t1, t2, ext, err = rename(filee)
            # print(t1,t2,ext)
            if err:
                self.loggin.emit("Error procesando: "+i, WARNING)
                continue
            if t2:
                fill = t1+' - '+str(t2)+ext
            else:
                fill = t1+ext
            if formatt.search(fill) or re.match('[0-9]+x?[0-9]*', fill, re.I):
                if isinstance(t2, str):
                    if 'x' in t2:
                        t2 = t2.split('x')[1]
                if fold in folds:
                    if t1 in folds[fold]:
                        if folds[fold][t1] < int(t2):
                            folds[fold][t1]=int(t2)
                    else:
                        folds[fold][t1] = int(t2)
                else:
                    folds[fold] = {}
                    folds[fold][t1] = int(t2)
        self.caps_list = folds

    def falta_caps(self):
        base = self.pathbar.text()
        l = os.listdir(base)
        proces = []
        folds = []
        for i in l:
            path = os.path.join(base, i)
            if os.path.isdir(path):
                folds.append(i)
        for i in folds:
            path = os.path.join(base, i)
            try:
                t = os.listdir(path)
                for j in t:
                    if os.path.isfile(os.path.join(path, j)) and (os.path.splitext(j)[1] in formats):
                        proces.append((j, i))
            except PermissionError as e:
                self.loggin.emit("Acceso denegado a"+i, ERROR)

        folds = {}
        for filee, fold in proces:
            # print(fold, filee)
            t1, t2, ext, err = rename(filee)
            # print(t1,t2,ext)
            if err:
                self.loggin.emit("Error procesando: "+i, WARNING)
                continue
            if t2:
                fill = t1+' - '+str(t2)+ext
            else:
                fill = t1+ext
            if formatt.search(fill) or re.match('[0-9]+x?[0-9]*', fill, re.I):
                if isinstance(t2, str):
                    if 'x' in t2:
                        t2 = t2.split('x')[1]
                if fold in folds:
                    if t1 in folds[fold]:
                        folds[fold][t1].append(int(t2))
                    else:
                        folds[fold][t1] = [int(t2)]
                else:
                    folds[fold] = {}
                    folds[fold][t1] = [int(t2)]
        #print(folds)

        self.caps_list = folds
