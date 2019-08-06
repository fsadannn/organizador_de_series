
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


class FTPManager(BaseManager):

    def __init__(self, host, user, password, port=21, logger=None):
        self.ftp = fs.open_fs('ftp://'+user+':'+password+'@'+host+':'+str(port))
        super(FTPManager, self).__init__(self.ftp, logger)


class FTPGui(QWidget):

    logginn = pyqtSignal(str, str, int)

    def __init__(self):
        super(FTPGui, self).__init__()
        self.cl = QVBoxLayout()
        self.loggin = Logger('FTPGui', self.logginn)

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
        self.iplable = QLabel('ip: ')
        self.ip = QLineEdit(self)
        self.ip.setValidator(QRegExpValidator(QRegExp('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'), self.ip))
        self.portlable = QLabel('puerto: ')
        self.port = QLineEdit(self)
        self.port.setValidator(QIntValidator(self.port))
        self.port.setText('21')
        conn = qta.icon(
            'mdi.lan-connect',
            color='orange',
            color_active='red')
        self.ftpcon = QPushButton(conn, "", self)
        tt.addWidget(self.iplable)
        tt.addWidget(self.ip)
        tt.addSpacing(10)
        tt.addWidget(self.portlable)
        tt.addWidget(self.port)
        tt.addSpacing(10)
        tt.addWidget(self.ftpcon)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.userlable = QLabel('usuario: ', self)
        self.user = QLineEdit(self)
        self.passwtlable = QLabel('contraseña: ', self)
        self.passw = QLineEdit(self)
        self.passw.setEchoMode(QLineEdit.Password)
        tt.addWidget(self.userlable)
        tt.addWidget(self.user)
        tt.addSpacing(10)
        tt.addWidget(self.passwtlable)
        tt.addWidget(self.passw)
        tt.addSpacing(10)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.local = QLabel('FTP: ')
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
        #self.configs = QToolButton(self)
        #self.configs.setPopupMode(QToolButton.InstantPopup)
        #self.confmenu = QMenu(self.configs)
        #tt.addWidget(self.configs)
        self.cl.addLayout(tt)

        # tt = QVBoxLayout()
        # tt2 = QHBoxLayout()
        # self.progresslabel = QLabel(self)
        # self.speedlabel = QLabel(self)
        # tt2.addWidget(self.progresslabel)
        # tt2.addWidget(self.speedlabel)
        # self.progress = QProgressBar(self)
        # self.progress.setMinimum(0)
        # self.progress.setMaximum(100)
        # tt.addLayout(tt2)
        # tt.addWidget(self.progress)
        # self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.ftpcon.clicked.connect(self.connectar)
        self.ftpm = None
        self.in_progress = False
        self.time = 0
        self.movethread = None

    def connectar(self):
        try:
            port = int(self.port.text())
        except:
            self.loggin.emit('Puerto incorrect', ERROR)
            return
        ip = self.ip.text()
        if len(ip.split('.')) != 4:
            self.loggin.emit('ip incorrect', ERROR)
            return
        try:
            self.ftpm = FTPManager(ip, self.user.text(), self.passw.text(), port, self.loggin)
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
        self.ftpm.last(base)
        self.loggin.emit('Buscando capítulos', INFORMATION)
        self.ftpm.find_nexts(self.pathbarftp.text())
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

        # if self.in_progress:
        #     self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
        #     return
        # self.in_progress = True
        # self.download()