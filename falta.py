import sys
import os

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtWidgets import QListWidget, QLineEdit, QButtonGroup
from utils import INFORMATION, WARNING, DEBUG, ERROR, formats, formatt
from utils import rename, editDistance


class Falta(QWidget):

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

        self.li = QListWidget()
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
                data = [0]+list(sorted(caps_list[i]))
                for j in range(len(data)-1):
                    if data[j+1]-data[j] > 1:
                        if data[j+1]-data[j] == 2:
                            txt = i + " : " + str(data[j]+1)
                        else:
                            txt = i + " : " + \
                                str(data[j]+1) + '-' + str(data[j+1]-1)
                        li.addItem(txt)
        else:
            self.last()
            caps_list = self.caps_list
            for i in sorted(caps_list.keys()):
                li.addItem(i + ' : ' + str(caps_list[i]))

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
            t = os.listdir(path)
            for j in t:
                if os.path.isfile(os.path.join(path, j)) and (os.path.splitext(j)[1] in formats):
                    proces.append((j, i))

        folds = {}
        for filee, fold in proces:
            if formatt.search(filee):
                t1, t2, ext, err = rename(filee)
                if err:
                    continue
                if fold in folds:
                    if folds[fold]<int(t2):
                        folds[fold]=int(t2)
                else:
                    folds[fold]=int(t2)
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
            t = os.listdir(path)
            for j in t:
                if os.path.isfile(os.path.join(path, j)) and (os.path.splitext(j)[1] in formats):
                    proces.append((j, i))

        folds = {}
        for filee, fold in proces:
            if formatt.search(filee):
                t1, t2, ext, err = rename(filee)
                if err:
                    continue
                if fold in folds:
                    folds[fold].append(int(t2))
                else:
                    folds[fold] = [int(t2)]
        self.caps_list = folds
