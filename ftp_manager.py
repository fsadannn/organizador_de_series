
from utils import INFORMATION, WARNING, DEBUG, ERROR, video_formats
from utils import rename, editDistance
from utils import parse_serie_guessit as parse
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
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
from sync import make_temp_fs
from copier import Copier
import fs
from fs.wrap import cache_directory, read_only
from fs.errors import RemoteConnectionError, IllegalBackReference
from threading import Thread
from fs.path import join, splitext, split, normpath, frombase
import qtawesome as qta


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

class FTPManager:

    def __init__(self, host, user, password, port=21, logger=None):
        self.ftp = cache_directory(read_only(fs.open_fs('ftp://'+user+':'+password+'@'+host+':'+str(port))))
        self.ftp.desc('/')
        self.caps_list = {}
        self.results = []
        self.logger = logger
        self.copier = Copier(num_workers=1)
        self.copier.start()

    def close(self):
        self.ftp.close()
        self.copier.stop()

    def list_dir(self, top):
        return [i.name for i in self.ftp.scandir(top) if i.is_dir]

    def download(self, src_pth, src_file , dest_pth, dest_file, call=None):

        ff = fs.open_fs(dest_pth)
        self.copier.copy(self.ftp, join(src_pth, src_file),
                        ff, join('/', dest_file),
                        call, inject_fs=True)

    def find_nexts(self, top='/', deep=0, maxdeep=2):
        if deep==0:
            self.results = []
        # print(top)
        if deep > maxdeep:
            return
        if self.logger:
            self.logger.emit(top, INFORMATION)
        dirs, nondirs = [], []
        for name in self.ftp.scandir(top):
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
            if not self.ftp.islink(path):
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
                    self.loggin.emit("Acceso denegado a"+join(base,i.name), ERROR)

            folds = {}
            for filee, fold in proces:
                fold = fold.name
                filee = filee.name
                try:
                    pp = parse(filee)
                except Exception as e:
                    self.loggin.emit("Error procesando: "+join(base,fold,filee), WARNING)
                    self.loggin.emit(str(e), ERROR)
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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ftp.close()
        self.copier.stop()
        return False


fff = re.compile('')
def filt(t):
    pass
    # funcion para capitulos en el formato temp[xX]caps


class FTPGui(QWidget):

    loggin = pyqtSignal(str, int)

    def __init__(self):
        super(FTPGui, self).__init__()
        self.cl = QVBoxLayout()

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
        self.cl.addLayout(tt)

        tt = QVBoxLayout()
        tt2 = QHBoxLayout()
        self.progresslabel = QLabel(self)
        self.speedlabel = QLabel(self)
        tt2.addWidget(self.progresslabel)
        tt2.addWidget(self.speedlabel)
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        tt.addLayout(tt2)
        tt.addWidget(self.progress)
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.ftpcon.clicked.connect(self.connectar)
        self.ftpm = None
        self.in_progress = False
        self.time = 0

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
        try:
            normpath(join(txt2,'..'))
            item = QListWidgetItem(qta.icon(
                    'fa5s.folder-open',
                    color='orange'), '..', self.li)
            self.li.addItem(item)
        except IllegalBackReference:
            pass
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
            self.ftpm.download(i[2], i[1], base, i[3], self.update)
        self.in_progress = False
        self.speedlabel.clear()
        #self.speedlabel.setText('')

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
        if self.in_progress:
            self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
            return
        self.in_progress = True
        self.download()