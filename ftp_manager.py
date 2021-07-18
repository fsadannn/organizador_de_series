
from utils import INFORMATION, WARNING, DEBUG, ERROR, video_formats
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtWidgets import QLabel, QProgressBar
from PyQt5.QtGui import QIntValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp
import fs
from fs.path import join, normpath
import qtawesome as qta
from sync import BaseManager
from utils import Logger, reconnect


class FTPManager(BaseManager):

    def __init__(self, host, user, password, port=21, logger=None):
        self.ftp = fs.open_fs('ftp://' + user + ':' +
                              password + '@' + host + ':' + str(port))
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
        self.pathbtn = QPushButton(folder, "", self)
        tt.addWidget(self.local)
        tt.addWidget(self.pathbar)
        tt.addWidget(self.pathbtn)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        self.iplable = QLabel('ip: ')
        self.ip = QLineEdit(self)
        self.ip.setValidator(QRegExpValidator(
            QRegExp('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'), self.ip))
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
        # self.configs.setPopupMode(QToolButton.InstantPopup)
        #self.confmenu = QMenu(self.configs)
        # tt.addWidget(self.configs)
        self.cl.addLayout(tt)

        tt = QVBoxLayout()
        tt3 = QHBoxLayout()
        self.namelabel = QLabel(self)
        tt3.addWidget(self.namelabel)
        tt2 = QHBoxLayout()
        self.progresslabel = QLabel(self)
        self.speedlabel = QLabel(self)
        tt2.addWidget(self.progresslabel)
        tt2.addWidget(self.speedlabel)
        self.progress = QProgressBar(self)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        tt.addLayout(tt3)
        tt.addLayout(tt2)
        tt.addWidget(self.progress)
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
        self.pathbtn.clicked.connect(self.set_path)
        self.proc.clicked.connect(self.procces)
        self.ftpcon.clicked.connect(self.connectar)
        self.ftpm = None
        self.in_progress = False

    @pyqtSlot()
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
            if self.ftpm:
                self.ftpm.close()
                reconnect(self.ftpm.copier.worker.names)
                reconnect(self.ftpm.copier.worker.progress)
                reconnect(self.ftpm.copier.worker.finish)
                reconnect(self.ftpm.copier.finish)
            self.ftpm = FTPManager(ip, self.user.text(),
                                   self.passw.text(), port, self.loggin)
            reconnect(self.ftpm.copier.worker.names, self.change_names)
            reconnect(self.ftpm.copier.worker.progress, self.update)
            reconnect(self.ftpm.copier.worker.finish, self.copy_finish2)
            reconnect(self.ftpm.copier.finish, self.copy_finish)
            self.pathbarftp.setText('/')
        except Exception as e:
            self.loggin.emit(str(e), ERROR)
            return
        self.li.clear()
        for i in self.ftpm.list_dir('/'):
            item = QListWidgetItem(qta.icon(
                'fa5s.folder-open',
                color='orange'), i, self.li)
            self.li.addItem(item)

    def ftp_move_to(self, item):
        txt = item.text()
        txt2 = normpath(join(self.pathbarftp.text(), txt))
        self.li.clear()
        if txt2 != '/':
            normpath(join(txt2, '..'))
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

    @pyqtSlot()
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
        self.in_progress = True
        self.ftpm.last(base)
        self.loggin.emit('Buscando capítulos', INFORMATION)
        self.ftpm.find_nexts(self.pathbarftp.text())
        r = self.ftpm.results
        for i in r:
            # ftpp = join(i[2],i[1])
            self.ftpm.download(i[2], i[1], base, i[3])

    @pyqtSlot(str, str)
    def change_names(self, src, dst):
        self.namelabel.setText(src + '    ' + dst)
        self.loggin.emit('Descargando ' + src + '  para  ' + dst, INFORMATION)

    @pyqtSlot(int, int, float)
    def update(self, total, count, speed):
        val = int(count / max(total, 1e-12) * 100)
        self.progress.setValue(val)
        self.speedlabel.setText(str(speed / (1024)) + ' Kb/s')

    @pyqtSlot()
    def copy_finish2(self):
        self.progress.setValue(100)
        self.loggin.emit('Descarga de archivo finalizada', INFORMATION)

    @pyqtSlot()
    def copy_finish(self):
        self.progress.setValue(0)
        self.speedlabel.clear()
        self.namelabel.clear()
        self.loggin.emit('Descarga finalizada', INFORMATION)
        self.in_progress = False

    @pyqtSlot()
    def procces(self):
        if self.in_progress:
            self.loggin.emit(
                'Hay un proceso en este momento, espere.', WARNING)
            return
        self.download()

        # if self.in_progress:
        #     self.loggin.emit('Hay un proceso en este momento, espere.', WARNING)
        #     return
        # self.in_progress = True
        # self.download()
