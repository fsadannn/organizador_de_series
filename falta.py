import sys
import os
import re
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtWidgets import QTreeWidget, QLineEdit, QButtonGroup
from PyQt5.QtWidgets import QTreeWidgetItem
from utils import INFORMATION, WARNING, DEBUG, ERROR
from utils import parse_serie_guessit as parse
from utils import rename as parse2
from utils import video_formats
from parser_serie import transform
import fs
from fs.path import join, splitext
from fs.wrap import read_only
from fs.errors import DirectoryExpected
import qtawesome as qta
from utils import Logger, best_ed


fff = re.compile('')


def filt(t):
    pass
    # funcion para capitulos en el formato temp[xX]caps


class Falta(QWidget):

    logginn = pyqtSignal(str, str, int)

    def __init__(self):
        super(Falta, self).__init__()
        self.cl = QVBoxLayout()
        self.loggin = Logger('FaltaGui', self.logginn)

        tt = QHBoxLayout()
        self.pathbar = QLineEdit()
        folder = qta.icon(
            'fa5s.folder-open',
            color='orange',
            color_active='red')
        self.pathbtn = QPushButton(folder, '')
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
        find = qta.icon(
            'fa5s.search',
            color='orange',
            color_active='red')
        self.proc = QPushButton(find, "")
        tt.addWidget(self.proc)
        tt.addStretch()
        save = qta.icon(
            'fa5s.save',
            color='black',
            color_active='red')
        self.save = QPushButton(save, "")
        tt.addWidget(self.save)
        self.cl.addLayout(tt)
        self.falta_txt = ''

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.li.itemExpanded.connect(self.change_open_icon)
        self.li.itemCollapsed.connect(self.change_close_icon)
        self.move.buttonClicked.connect(self.chnage_option)
        self.save.clicked.connect(self.save_falta)

    @pyqtSlot()
    def save_falta(self):
        if self.pathbar.text() == '':
            return
        with open(os.path.join(self.pathbar.text(), 'falta.txt'), 'w') as f:
            f.write(self.falta_txt)

    def chnage_option(self, idd):
        if self.move.checkedId() == 1:
            self.save.show()
        else:
            self.save.hide()

    def change_open_icon(self, item):
        folder = qta.icon(
            'fa5s.folder-open',
            color='orange')
        item.setIcon(0, folder)

    def change_close_icon(self, item):
        folder = qta.icon(
            'fa5s.folder',
            color='orange')
        item.setIcon(0, folder)

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

    @pyqtSlot()
    def set_path(self):
        dirr = self.get_path()
        if dirr is None or dirr == '':
            return
        self.pathbar.setText(dirr)

    @pyqtSlot()
    def procces(self):
        if self.pathbar.text() == '':
            return
        folder = qta.icon(
            'fa5s.folder',
            color='orange')
        video = qta.icon(
            'fa5s.file-video',
            color='blue')
        li = self.li
        li.clear()
        if self.move.checkedId() == 1:
            self.falta_caps()
            falta_txt = ''
            falta_set = set()
            caps_list = self.caps_list
            for i in sorted(caps_list.keys()):
                parent = QTreeWidgetItem()
                parent.setIcon(0, folder)
                parent.setText(0, i)
                addp = False
                for k in sorted(caps_list[i].keys()):
                    data = [0] + list(sorted(caps_list[i][k]))
                    for j in range(len(data) - 1):
                        if data[j + 1] - data[j] > 1:
                            if data[j + 1] - data[j] == 2:
                                if not(k in falta_set):
                                    falta_set.add(k)
                                    falta_txt += '\n' + k + ':  '
                                    falta_txt += str(data[j] + 1)
                                else:
                                    falta_txt += ', ' + str(data[j] + 1)
                                txt = k + " : " + str(data[j] + 1)
                                addp = True
                            else:
                                if not(k in falta_set):
                                    falta_set.add(k)
                                    falta_txt += '\n' + k + ':  '
                                    falta_txt += str(data[j] + 1) + \
                                        '-' + str(data[j + 1] - 1)
                                else:
                                    falta_txt += ', ' + \
                                        str(data[j] + 1) + '-' + \
                                        str(data[j + 1] - 1)
                                txt = k + " : " + \
                                    str(data[j] + 1) + '-' + \
                                    str(data[j + 1] - 1)
                                addp = True
                            child = QTreeWidgetItem(parent)
                            child.setIcon(0, video)
                            child.setText(0, txt)
                            parent.addChild(child)
                self.falta_txt = falta_txt + '\n'
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
                parent.setIcon(0, folder)
                parent.setText(0, i)
                for k in sorted(caps_list[i].keys()):
                    txt = k + " - " + str(caps_list[i][k])
                    child = QTreeWidgetItem(parent)
                    child.setIcon(0, video)
                    child.setText(0, txt)
                    parent.addChild(child)
                li.addTopLevelItem(parent)

    def last(self):
        base = self.pathbar.text()
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
                    self.loggin.emit("Acceso denegado a" +
                                     join(base, i.name), ERROR)

            folds = {}
            for filee, fold in proces:
                fold = fold.name
                filee = filee.name
                self.loggin.emit("Procesando: " +
                                 join(base, fold), INFORMATION)
                try:
                    pp = parse2(filee)
                    if pp.error:
                        pp = parse(filee)
                except Exception as e:
                    self.loggin.emit("Error procesando: " +
                                     join(base, fold, filee), WARNING)
                    self.loggin.emit(e, ERROR)
                    continue
                t1 = transform(pp.title)
                # fill = t1
                if not pp.episode:
                    continue
                t2 = pp.episode
                if fold in folds:
                    if t1 in folds[fold]:
                        if folds[fold][t1] < int(t2):
                            folds[fold][t1] = int(t2)
                    else:
                        tt = best_ed(t1, folds[fold].keys(), gap=2)
                        if tt in folds[fold]:
                            if folds[fold][tt] < int(t2):
                                folds[fold][tt] = int(t2)
                        else:
                            folds[fold][tt] = int(t2)
                else:
                    folds[fold] = {}
                    folds[fold][t1] = int(t2)
            self.caps_list = folds

    def falta_caps(self):
        base = self.pathbar.text()
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
                    self.loggin.emit("Acceso denegado a" +
                                     join(base, i.name), ERROR)

            folds = {}
            for filee, fold in proces:
                fold = fold.name
                filee = filee.name
                self.loggin.emit("Procesando: " +
                                 join(base, fold), INFORMATION)
                try:
                    pp = parse2(filee)
                    if pp.error:
                        pp = parse(filee)
                except Exception as e:
                    self.loggin.emit("Error procesando: " +
                                     join(base, fold, filee), WARNING)
                    self.loggin.emit(e, ERROR)
                    continue
                t1 = transform(pp.title)
                if not pp.episode:
                    continue
                t2 = pp.episode
                if fold in folds:
                    if t1 in folds[fold]:
                        folds[fold][t1].add(int(t2))
                    else:
                        tt = best_ed(t1, folds[fold].keys(), gap=2)
                        if tt in folds[fold]:
                            folds[fold][tt].add(int(t2))
                        else:
                            folds[fold][tt] = set()
                            folds[fold][tt].add(int(t2))
                else:
                    folds[fold] = {}
                    folds[fold][t1] = set()
                    folds[fold][t1].add(int(t2))
            # for i in folds.keys():
            #     for j in folds[i]:
            #         folds[i][j]=list(set(folds[i][j]))
            self.caps_list = folds
