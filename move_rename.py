import sys
import os
from threading import Thread
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton
from PyQt5.QtWidgets import QListWidget, QButtonGroup, QRadioButton
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from utils import INFORMATION, WARNING, DEBUG, ERROR
from utils import rename
from sync import make_temp_fs
import fs
from fs.path import join, split
import qtawesome as qta
from utils import Logger


if hasattr(sys, 'frozen'):
    MODULE = os.path.dirname(sys.executable)
else:
    try:
        MODULE = os.path.dirname(os.path.realpath(__file__))
    except:
        MODULE = ""


class MoveRename(QWidget):

    logginn = pyqtSignal(str, str, int)

    def __init__(self):
        super(MoveRename, self).__init__()
        self.loggin = Logger('MoveRenameGui', self.logginn)
        self.cl = QVBoxLayout()

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
        selall = qta.icon(
            'mdi.select-all',
            color='blue',
            color_active='red')
        self.all = QPushButton(selall, '')
        selinv = qta.icon(
            'mdi.select-inverse',
            color='blue',
            color_active='red')
        self.invert = QPushButton(selinv, "")
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
        procc = qta.icon(
            'mdi.play',
            color='green',
            color_active='red')
        self.proc = QPushButton(procc, "")
        tt.addWidget(self.proc)
        tt.addStretch()
        self.cl.addLayout(tt)

        self.setLayout(self.cl)

        self.pathbtn.clicked.connect(self.set_path)
        self.li.itemClicked.connect(self.check_item)
        self.all.clicked.connect(self.allf)
        self.invert.clicked.connect(self.invertf)
        self.move.buttonClicked.connect(self.gen_list)
        self.proc.clicked.connect(self.procces)
        self.movethread = None

    def gen_list(self, id):
        if self.pathbar.text() == '':
            return
        self.build_ui_caps()
        self.allf()

    @pyqtSlot()
    def allf(self):
        li = self.li
        if li.count() == 0:
            return
        cpsm = self.capsmap
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                txt = item.text().split("\t")
                cpsm[txt[1]]['state'] = True

    @pyqtSlot()
    def invertf(self):
        li = self.li
        if li.count() == 0:
            return
        cpsm = self.capsmap
        for i in range(li.count()):
            item = li.item(i)
            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                txt = item.text().split("\t")
                cpsm[txt[1]]['state'] = True
            else:
                item.setCheckState(Qt.Unchecked)
                txt = item.text().split("\t")
                cpsm[txt[1]]['state'] = False

    def check_item(self, item):
        cpsm = self.capsmap
        if item.checkState() == Qt.Unchecked:
            item.setCheckState(Qt.Checked)
            txt = item.text().split("\t")
            cpsm[txt[1]]['state'] = True
        else:
            item.setCheckState(Qt.Unchecked)
            txt = item.text().split("\t")
            cpsm[txt[1]]['state'] = False

    def edititem(self, item):
        cpsm = self.capsmap
        txt = item.text().split("\t")
        text, ok = QInputDialog.getText(None, "Editar",
                                        "Nombre:", QLineEdit.Normal,
                                        txt[0])
        if ok and text != '' and not(text is None):
            if text == txt[0]:
                return
            pth = cpsm[txt[1]]['vpath']
            pth2 = join(split(pth)[0], text)
            try:
                self.vfs.move(pth, pth2)
            except fs.errors.DestinationExists:
                self.loggin.emit(
                    'Ya existe otro fichero que tiene este posible nombre', ERROR)
                return
            cpsm[txt[1]]['vpath'] = pth2
            cpsm[txt[1]]['fixname'] = text
            item.setText(text + '\t' + txt[1])
            item.setCheckState(Qt.Checked)
            cpsm[txt[1]]['state'] = True

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
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', WARNING)
                return
        dirr = self.get_path()
        if dirr is None or dirr == '':
            return
        self.dirr = dirr
        self.pathbar.setText(dirr)
        self.build_ui_caps()
        self.allf()

    def build_ui_caps(self):
        dirr = self.dirr
        with fs.open_fs(dirr) as f:
            data = make_temp_fs(f)
        self.vfs = data
        capsmap = {}
        vfs = self.vfs
        # vfs.tree()
        for path, _, files in vfs.walk():
            for i in files:
                dd = {}
                nn = i.name
                pp = rename(nn)
                dd['fixname'] = nn
                dd['cap'] = pp.episode
                dd['season'] = pp.season
                opth = vfs.gettext(join(path, nn))
                oon = split(opth)[1]
                dd['original'] = oon
                dd['ext'] = pp.ext.lower()
                dd['vpath'] = join(path, nn)
                dd['state'] = True
                dd['fold'] = split(path)[1]
                capsmap[oon] = dd
        self.capsmap = capsmap
        nonly = self.move.checkedId() == 3
        li = self.li
        lic = li.count()
        cps = list(capsmap.values())
        cpl = len(cps)
        if cpl <= lic:
            for n, i in enumerate(cps):
                name = i['fixname']
                if nonly:
                    name = i['cap'] + i['ext']
                ll = li.item(n)
                ll.setText(name + "\t" + i['original'])
            for i in range(lic - cpl):
                ll = li.takeItem(0)
                del ll
        else:
            for i in range(lic):
                name = cps[i]['fixname']
                if nonly:
                    name = i['cap'] + i['ext']
                ll = li.item(i)
                ll.setText(name + "\t" + cps[i]['original'])
            for i in range(cpl - lic):
                name = cps[lic + i]['fixname']
                if nonly:
                    name = i['cap'] + i['ext']
                li.addItem(name + "\t" + cps[lic + i]['original'])

    @pyqtSlot()
    def procces(self):
        if self.pathbar.text() == '':
            return
        if self.move.checkedId() == 1:
            self.movef(self.pathbar.text())
        else:
            self.renamef(self.pathbar.text())

    def movef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', WARNING)
                return
        self.movethread = Thread(target=self._movef, args=(path,))
        self.movethread.start()

    def renamef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', WARNING)
                return
        self.movethread = Thread(target=self._renamef, args=(path,))
        self.movethread.start()

    def _movef(self, path):
        # ram = self.vfs
        with fs.open_fs(path) as ff:
            for data in self.capsmap.values():
                if not data['state']:
                    continue
                fold = data['fold']
                path = join('/', fold)
                if not(ff.exists(path)):
                    ff.makedir(path)
                path2 = join(path, data['fixname'])
                opth = join('/', data['original'])
                self.loggin.emit("Moviendo y renombrando: " + data['original'] + ' para ' + join(
                    data['fold'], data['fixname']), INFORMATION)
                try:
                    ff.move(opth, path2, True)
                except Exception as e:
                    self.loggin.emit("Error en archivo: " +
                                     data['original'] + '<br>' + str(e), ERROR)
        self.loggin.emit("Mover finalizado.", DEBUG)
        self.build_ui_caps()
        self.allf()

    def _renamef(self, path):
        with fs.open_fs(path) as ff:
            for data in self.capsmap.values():
                if not data['state']:
                    continue
                if data['fixname'] == data['original']:
                    continue
                path = '/'
                path2 = join(path, data['fixname'])
                opth = join(path, data['original'])
                self.loggin.emit(
                    "Renombrando: " + data['original'] + ' a ' + data['fixname'], INFORMATION)
                try:
                    ff.move(opth, path2, overwrite=True)
                except Exception as e:
                    self.loggin.emit("Error en archivo: " +
                                     split(opth)[1] + '<br>' + str(e), ERROR)
        self.loggin.emit("Renombrar finalizado.", DEBUG)
        self.build_ui_caps()
        self.allf()
