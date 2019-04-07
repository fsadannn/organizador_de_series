import ftplib
import ftputil
from utils import INFORMATION, WARNING, DEBUG, ERROR, formats, formatt
from utils import rename, editDistance
import os
import re
import sys
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtWidgets import QListWidget, QLineEdit, QButtonGroup
from PyQt5.QtWidgets import QLabel, QProgressBar
from threading import Thread

def points(name):
    if re.search('anime|managa',name,re.I) :
        return 0
    if re.search('trasmi|transmi|tx',name,re.I):
        return 1
    return 2

class Wrapper:
    def __init__(self, total, callback):
        self.total = total
        self.acum = 0
        self.callback = callback
    def __call__(self, data):
        self.acum+=len(data)
        percent = int(self.acum/self.total*100)
        self.callback(percent)

class MySession(ftplib.FTP):

    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


#ftputil.FTPHost(host, userid, password, port=port, session_factory=MySession)

class FTPManager:

    def __init__(self, host, user, password, port=21, logger=None):
        self.ftp = ftputil.FTPHost(
            host, user, password, port=port, session_factory=MySession)
        self.caps_list = {}
        self.results = []
        self.logger = logger

    def list_dir(self, top):
        top = ftputil.tool.as_unicode(top)
        try:
            names = self.ftp.listdir(top)
        except ftputil.error.FTPOSError as err:
            if logger:
                self.logger.emit(str(err),ERROR)
        dirs = []
        for name in names:
            if self.ftp.path.isdir(self.ftp.path.join(top, name)):
                dirs.append(name)
        return dirs

    def download(self, patha, base, call=None):
        st = self.ftp.stat(patha)
        sz = st.st_size
        if call:
            wrap = Wrapper(sz, call)
            self.ftp.download(patha, base, wrap)
        else:
            self.ftp.download(patha, base)


    def find_nexts(self, top='/', deep=0, maxdeep=2):
        if deep==0:
            self.results = []
        top = ftputil.tool.as_unicode(top)
        # print(top)
        if deep > maxdeep:
            return
        if self.logger:
            self.logger.emit(top, INFORMATION)
        try:
            names = self.ftp.listdir(top)
        except ftputil.error.FTPOSError as err:
            if logger:
                self.logger.emit(str(err),ERROR)
            return
        dirs, nondirs = [], []
        for name in names:
            if self.ftp.path.isdir(self.ftp.path.join(top, name)):
                dirs.append(name)
            elif self.ftp.path.splitext(name)[1] in formats:
                nondirs.append(name)
        # print(dirs,nondirs)
        for fil in nondirs:
            t1, t2, ext, err = rename(fil)
            # print(t1,t2,ext)
            if err:
                if self.logger:
                    self.logger.emit("Error procesando: "+i, WARNING)
                continue
            best = None
            bd = 100
            for j in self.caps_list.keys():
                d1 = editDistance(j,t1, False)
                d2 = editDistance(j,t1,True)
                if d1<4 or d2<=2:
                    bdt = 10*d1+d2
                    if isinstance(t2, str):
                        if 'x' in t2:
                            t2 = t2.split('x')[1]
                    if bdt<bd and int(t2)>self.caps_list[j]:
                        best = (j, fil, top)
            if best:
                self.results.append(best)
                if self.logger:
                    self.logger.emit('Encontrado: '+str(best), INFORMATION)

        def skey(a):
            if re.search('anime|manga',a,re.I):
                return 0
            else:
                return 1
        for name in sorted(dirs,key=skey):
            path = self.ftp.path.join(top, name)
            if not self.ftp.path.islink(path):
                self.find_nexts(path, deep+1, maxdeep)

    def last(self, base):
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
                if self.loggin:
                    try:
                        self.logger.emit("Acceso denegado a"+i, ERROR)
                    except:
                        self.logger.error("Acceso denegado a"+i)

        folds = {}
        for filee, fold in proces:
            # print(fold, filee)
            t1, t2, ext, err = rename(filee)
            # print(t1,t2,ext)
            if err:
                if self.logger:
                    try:
                        self.logger.emit("Error procesando: "+i, WARNING)
                    except:
                        self.logger.warning("Error procesando: "+i)
                continue
            if t2:
                fill = t1+' - '+str(t2)+ext
            else:
                fill = t1+ext
            if formatt.search(fill) or re.match('[0-9]+x?[0-9]*', fill, re.I):
                if isinstance(t2, str):
                    if 'x' in t2:
                        t2 = t2.split('x')[1]
                if t1 in folds:
                    if folds[t1] < int(t2):
                        folds[t1] = int(t2)
                else:
                    folds[t1] = int(t2)
        self.caps_list = folds

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ftp.close()
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
        self.local = QLabel('Local: ')
        self.pathbar = QLineEdit()
        self.pathbtn = QPushButton("Cambiar")
        tt.addWidget(self.local)
        tt.addWidget(self.pathbar)
        tt.addWidget(self.pathbtn)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.iplable = QLabel('ip: ')
        self.ip = QLineEdit()
        self.portlable = QLabel('puerto: ')
        self.port = QLineEdit()
        self.ftpcon = QPushButton("Conectar")
        tt.addWidget(self.iplable)
        tt.addWidget(self.ip)
        tt.addSpacing(10)
        tt.addWidget(self.portlable)
        tt.addWidget(self.port)
        tt.addSpacing(10)
        tt.addWidget(self.ftpcon)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.userlable = QLabel('usuario: ')
        self.user = QLineEdit()
        self.passwtlable = QLabel('contraseña: ')
        self.passw = QLineEdit()
        tt.addWidget(self.userlable)
        tt.addWidget(self.user)
        tt.addSpacing(10)
        tt.addWidget(self.passwtlable)
        tt.addWidget(self.passw)
        tt.addSpacing(10)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.local = QLabel('FTP: ')
        self.pathbarftp = QLineEdit()
        tt.addWidget(self.local)
        tt.addWidget(self.pathbarftp)
        self.cl.addLayout(tt)

        self.li = QListWidget()
        self.cl.addWidget(self.li)
        self.li.itemDoubleClicked.connect(self.ftp_move_to)

        tt = QHBoxLayout()
        self.proc = QPushButton("Buscar")
        tt.addWidget(self.proc)
        tt.addStretch()
        self.cl.addLayout(tt)

        tt = QVBoxLayout()
        self.progresslabel = QLabel()
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        tt.addWidget(self.progresslabel)
        tt.addWidget(self.progress)
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.ftpcon.clicked.connect(self.connectar)
        self.ftpm = None
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
            self.li.addItem(i)

    def ftp_move_to(self, item):
        txt = item.text()
        if txt == '..':
            self.ftpm.ftp.chdir('..')
            self.li.clear()
            if self.ftpm.ftp.getcwd() != '/':
                self.li.addItem('..')
            for i in self.ftpm.list_dir(self.ftpm.ftp.getcwd()):
                self.li.addItem(i)
        else:
            self.ftpm.ftp.chdir(txt)
            self.li.clear()
            self.li.addItem('..')
            for i in self.ftpm.list_dir(self.ftpm.ftp.getcwd()):
                self.li.addItem(i)
        self.pathbarftp.setText(self.ftpm.ftp.getcwd())


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
            return
        if not self.ftpm:
            return
        self.ftpm.last(base)
        self.loggin.emit('Buscando capítulos', INFORMATION)
        self.ftpm.find_nexts(self.pathbarftp.text())
        r = self.ftpm.results
        for i in r:
            ftpp = self.ftpm.ftp.path.join(i[2],i[1])
            self.progresslabel.setText(ftpp)
            self.progress.setValue(0)
            self.ftpm.download(ftpp, os.path.join(base,i[1]), self.progress.setValue)

    def procces(self):
        # if self.movethread:
        #     if self.movethread.isAlive():
        #         self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
        #         return
        # self.movethread = Thread(target=self.download)
        # self.movethread.start()
        self.download()

# f = FTPManager('127.0.0.1','test','1234',21)
# def a(t):
#     print(t)
# f.download('/Mikosch.pdf','./Mikosch.pdf',a)