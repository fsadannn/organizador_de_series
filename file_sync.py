
from utils import INFORMATION, WARNING, DEBUG, ERROR, video_formats
from utils import rename, editDistance
from utils import parse_serie_guessit as parse
from utils import rename as parse2
from parser_serie import transform
import os
import re
import sys
import time
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtWidgets import QLineEdit, QButtonGroup
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtWidgets import QLabel, QProgressBar
from PyQt5.QtWidgets import QToolButton, QMenu
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
import fs
from threading import Thread
from fs.path import join, splitext, split, normpath, frombase
import qtawesome as qta
from sync import BaseManager
from utils import Logger


class FileManager(BaseManager):

    def __init__(self, path, logger=None):
        self.file = fs.open_fs(path)
        super(FileManager, self).__init__(self.file, logger)


class FileGui(QWidget):

    logginn = pyqtSignal(str, str, int)

    def __init__(self):
        super(FileGui, self).__init__()
        self.cl = QVBoxLayout()
        self.loggin = Logger('FileGui', self.logginn)

        tt = QHBoxLayout()
        self.local = QLabel('Local: ', self)
        self.pathbar = QLineEdit(self)
        folder = qta.icon(
            'fa5s.folder-open',
            color='orange',
            color_active='red')
        self.pathbtn = QPushButton(folder ,"", self)
        tt.addWidget(self.local)
        tt.addWidget(self.pathbar)
        tt.addWidget(self.pathbtn)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.other = QLabel('Otro: ', self)
        self.pathbar2 = QLineEdit(self)
        folder = qta.icon(
            'fa5s.folder-open',
            color='orange',
            color_active='red')
        self.pathbtn2 = QPushButton(folder ,"", self)
        tt.addWidget(self.other)
        tt.addWidget(self.pathbar2)
        tt.addWidget(self.pathbtn2)
        self.cl.addLayout(tt)


        tt = QHBoxLayout()
        self.local = QLabel('Folders: ')
        self.pathbarftp = QLineEdit(self)
        self.pathbarftp.setReadOnly(True)
        tt.addWidget(self.local)
        tt.addWidget(self.pathbarftp)
        self.cl.addLayout(tt)

        self.li = QListWidget(self)
        self.cl.addWidget(self.li)
        self.li.itemDoubleClicked.connect(self.ftp_move_to)

        tt = QHBoxLayout()
        find = qta.icon(
            'fa5s.search',
            color='orange',
            color_active='red')
        self.proc = QPushButton(find, "", self)
        tt.addWidget(self.proc)
        tt.addStretch()
        self.move = QButtonGroup()
        tt1 = QRadioButton("Todos")
        tt2 = QRadioButton("Último")
        tt2.setChecked(True)
        self.move.addButton(tt1, 2)
        self.move.addButton(tt2, 1)
        self.move.setExclusive(True)
        tt.addWidget(tt1)
        tt.addWidget(tt2)
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.pathbtn2.clicked.connect(self.set_path2)
        self.ftpm = None
        self.in_progress = False
        self.time = 0
        self.movethread = None


    def set_path2(self):
        dirr = self.get_path()
        if dirr is None or dirr == '':
            return
        self.pathbar2.setText(dirr)
        try:
            self.ftpm = FileManager(dirr, self.loggin)
            self.pathbarftp.setText('/')
        except Exception as e:
            self.loggin.emit(str(e),ERROR)
            return
        self.li.clear()
        for i in self.ftpm.list_dir('/'):
            item = QListWidgetItem(qta.icon(
                    'fa5s.folder-open',
                    color='orange'), i, self.li)
            self.li.addItem(item)

    def ftp_move_to(self, item):
        txt = item.text()
        txt2 = normpath(join(self.pathbarftp.text(),txt))
        self.li.clear()
        if txt2 != '/':
            normpath(join(txt2,'..'))
            item = QListWidgetItem(qta.icon(
                    'fa5s.folder-open',
                    color='orange'), '..', self.li)
            self.li.addItem(item)
        for i in self.ftpm.list_dir(txt2):
            item = QListWidgetItem(qta.icon(
                    'fa5s.folder-open',
                    color='orange'), i, self.li)
            self.li.addItem(item)
        self.pathbarftp.setText(txt2)


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

    def download(self):
        base = self.pathbar.text()
        if base == '':
            self.in_progress = False
            return
        if not self.ftpm:
            self.in_progress = False
            return
        if self.move.checkedId() == 1:
            self.ftpm.last(base)
        else:
            self.ftpm.last2(base)
        self.loggin.emit('Buscando capítulos', INFORMATION)
        if self.move.checkedId() == 1:
            self.ftpm.find_nexts(self.pathbarftp.text())
        else:
            self.ftpm.find_nexts2(self.pathbarftp.text())
        r = self.ftpm.results
        for i in r:
            ftpp = join(i[2],i[1])
            #self.ftpm.download(i[2], i[1], base, i[3], self.update)
            self.ftpm.download(i[2], i[1], base, i[3])
            self.loggin.emit('Descargando '+ i[1]  , INFORMATION)
        self.in_progress = False
        #self.speedlabel.clear()
        #self.speedlabel.setText('')
        self.loggin.emit('Descarga finalizada', INFORMATION)

    def update(self, data):
        if self.time == 0:
            self.progresslabel.setText(data.src)
            self.progress.setValue(0)
            val = int(data.percent)
            self.progress.setValue(val)
            val = data.speed/1024
            self.speedlabel.setText(str(val)+' Kb/s')
            self.time = time.time()
        else:
            tt = time.time()
            if tt-self.time>2:
                val = int(data.percent)
                self.progress.setValue(val)
                val = data.speed/1024
                self.speedlabel.setText(str(val)+' Kb/s')
                self.time = tt
        if data.finish:
            data.dst_fs.close()
            self.time = 0

    def procces(self):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
                return
        self.movethread = Thread(target=self.download)
        self.movethread.start()