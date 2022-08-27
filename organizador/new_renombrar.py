from threading import Thread
from typing import Dict, List

import qtawesome as qta
from fs.base import FS
from fs.errors import DestinationExists
from fs.osfs import OSFS
from fs.path import join, split
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QWidget,
)

from . import ui as UIs
from .utils.formats import get_ext
from .utils.qt_utils import Logger, LogLevel
from .utils.rename import ChapterMap, rename
from .utils.resource_loader import get_as_file_like_string
from .utils.sync import make_temp_fs


class Renombrar(QWidget):
    logginn = pyqtSignal(str, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loggin = Logger('Mover y Renombrar', self.logginn)
        self.movethread: Thread = None
        self.vfs: FS = None
        self.chapters_map: Dict[str, ChapterMap] = {}
        self.root_dir: str = ''

        ui_file = get_as_file_like_string(UIs, 'renombrar.ui')
        uic.loadUi(ui_file, self)

        folderIcon = qta.icon(
            'fa5s.folder-open',
            color='orange',
            color_active='red')
        btn: QPushButton = self.pathbtn
        btn.setText('')
        btn.setIcon(folderIcon)

        selallIcon = qta.icon(
            'mdi.select-all',
            color='blue',
            color_active='red')
        btn: QPushButton = self.selectAllButton
        btn.setText('')
        btn.setIcon(selallIcon)

        selinvIcon = qta.icon(
            'mdi.select-inverse',
            color='blue',
            color_active='red')
        btn: QPushButton = self.selectInvertButton
        btn.setText('')
        btn.setIcon(selinvIcon)

        procIcon = qta.icon(
            'mdi.play',
            color='green',
            color_active='red')

        btn: QPushButton = self.procButton
        btn.setText('')
        btn.setIcon(procIcon)

        self.moveGroup = QButtonGroup()
        self.moveGroup.addButton(self.moverRadio, 1)
        self.moveGroup.addButton(self.renombrarRadio, 2)
        self.moveGroup.setExclusive(True)

        self.pathbtn.clicked.connect(self.set_path)
        self.selectAllButton.clicked.connect(self.allf)
        self.selectInvertButton.clicked.connect(self.invertf)
        self.moveGroup.buttonClicked.connect(self.gen_list)
        self.listWidget.itemChanged.connect(self.check_item)
        self.listWidget.itemDoubleClicked.connect(self.edititem)
        self.procButton.clicked.connect(self.procces)

    @pyqtSlot()
    def invertf(self):
        li: QListWidget = self.listWidget
        if li.count() == 0:
            return

        cpsm = self.chapters_map

        for i in range(li.count()):
            item = li.item(i)

            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                txt = item.text().split("\t")
                cpsm[txt[1]].state = True
            else:
                item.setCheckState(Qt.Unchecked)
                txt = item.text().split("\t")
                cpsm[txt[1]].state = False

    @pyqtSlot()
    def allf(self):
        li: QListWidget = self.listWidget

        if li.count() == 0:
            return

        cpsm = self.chapters_map

        for i in range(li.count()):
            item = li.item(i)

            if item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)
                txt = item.text().split("\t")
                cpsm[txt[1]].state = True

    def _get_path(self):
        txt = self.pathbar.text()
        if txt is None or txt == "":
            txt = ""
        root_dir = QFileDialog.getExistingDirectory(self, "Selecionar Directorio",
                                                    txt,
                                                    QFileDialog.ShowDirsOnly
                                                    | QFileDialog.DontResolveSymlinks)
        # print(dirr)
        return root_dir

    @pyqtSlot()
    def set_path(self):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', LogLevel.WARNING)
                return
        root_dir = self._get_path()
        if root_dir is None or root_dir == '':
            return
        self.root_dir = root_dir
        self.pathbar.setText(root_dir)
        self._build_ui_caps()
        self.allf()

    def _build_ui_caps(self):
        root_dir = self.root_dir
        with OSFS(root_dir) as f:
            data = make_temp_fs(f)
        self.vfs: FS = data
        chapters_map: Dict[str, ChapterMap] = {}
        vfs = self.vfs
        vfs.tree()

        for path, _, files in vfs.walk():
            for i in files:
                name = i.name
                serie = rename(name)
                opth = vfs.gettext(join(path, name))
                oon = split(opth)[1]
                dd = {}
                dd['fixname'] = name
                dd['chapter'] = serie.episode
                dd['season'] = serie.season
                dd['original'] = oon
                dd['ext'] = get_ext(name)
                dd['vpath'] = join(path, name)
                dd['state'] = True
                dd['fold'] = split(path)[1]
                chapters_map[oon] = ChapterMap(**dd)

        self.chapters_map = chapters_map
        li: QListWidget = self.listWidget
        list_count: int = li.count()
        chapters: List[ChapterMap] = list(chapters_map.values())
        chapters_count: int = len(chapters)

        if chapters_count <= list_count:
            for n, i in enumerate(chapters):
                name = i.fixname
                ll = li.item(n)
                ll.setText(name + "\t" + i.original)
            for i in range(list_count - chapters_count):
                ll = li.takeItem(0)
                del ll
        else:
            for i in range(list_count):
                name = chapters[i].fixname
                ll = li.item(i)
                ll.setText(name + "\t" + chapters[i].original)
            for i in range(chapters_count - list_count):
                name = chapters[list_count + i].fixname
                li.addItem(name + "\t" + chapters[list_count + i].original)

    @pyqtSlot(QAbstractButton)
    def gen_list(self, button: QAbstractButton):
        if self.pathbar.text() == '':
            return
        self._build_ui_caps()
        self.allf()

    @pyqtSlot(QListWidgetItem)
    def check_item(self, item: QListWidgetItem):
        cpsm = self.chapters_map

        if item.checkState() == Qt.Unchecked:
            txt = item.text().split("\t")
            cpsm[txt[1]].state = False
        else:
            txt = item.text().split("\t")
            cpsm[txt[1]].state = True

    @pyqtSlot(QListWidgetItem)
    def edititem(self, item: QListWidgetItem):
        cpsm = self.chapters_map
        txt = item.text().split("\t")
        text, ok = QInputDialog.getText(None, "Editar",
                                        "Nombre:", QLineEdit.Normal,
                                        txt[0])
        if ok and text != '' and text is not None:
            if text == txt[0]:
                return

            pth = cpsm[txt[1]].vpath
            pth2 = join(split(pth)[0], text)

            try:
                self.vfs.move(pth, pth2)
            except DestinationExists:
                self.loggin.emit(
                    'Ya existe otro fichero que tiene este posible nombre', LogLevel.ERROR.value)
                return

            cpsm[txt[1]].vpath = pth2
            cpsm[txt[1]].fixname = text
            item.setText(text + '\t' + txt[1])
            item.setCheckState(Qt.Checked)
            cpsm[txt[1]].state = True

    @pyqtSlot()
    def procces(self):
        if self.pathbar.text() == '':
            return

        if self.moveGroup.checkedId() == 1:
            self.movef(self.pathbar.text())
        else:
            self.renamef(self.pathbar.text())

    def renamef(self, path: str):
        if self.movethread:
            if self.movethread.is_alive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', LogLevel.WARNING.value)
                return

        self.movethread = Thread(target=self._renamef, args=(path,))
        self.movethread.start()

    def _renamef(self, path: str):
        with OSFS(path) as ff:
            for data in self.chapters_map.values():
                if not data.state:
                    continue

                if data.fixname == data.original:
                    continue

                path = '/'
                path2 = join(path, data.fixname)
                opth = join(path, data.original)
                self.loggin.emit(
                    f'Renombrando: "{data.original}" a "{data.fixname}"', LogLevel.INFORMATION.value)

                try:
                    ff.move(opth, path2, overwrite=True)
                except Exception as e:
                    self.loggin.emit(
                        f'Error en archivo: {split(opth)[1]}<br>{str(e)}', LogLevel.ERROR.value)

        self.loggin.emit("Renombrar finalizado.", LogLevel.DEBUG.value)
        # re-generate list, this signal trigger the gen_list slot
        # call directly from thread can crash qt and also create throw
        # QObject::connect: Cannot queue arguments of type 'QVector<int>'
        self.moveGroup.buttonClicked.emit(self.moverRadio)

    def movef(self, path):
        if self.movethread:
            if self.movethread.isAlive():
                self.loggin.emit(
                    'Hay un proceso en este momento, espere.', LogLevel.WARNING.value)
                return
        self.movethread = Thread(target=self._movef, args=(path,))
        self.movethread.start()

    def _movef(self, path):
        # ram = self.vfs
        with OSFS(path) as ff:
            for data in self.chapters_map.values():
                if not data.state:
                    continue

                fold = data.fold
                path = join('/', fold)
                if not(ff.exists(path)):
                    ff.makedir(path)

                path2 = join(path, data.fixname)
                opth = join('/', data.original)
                self.loggin.emit(
                    f'Moviendo y renombrando: "{data.original}" para "{join(data.fold, data.fixname)}"', LogLevel.INFORMATION.value)

                try:
                    ff.move(opth, path2, True)
                except Exception as e:
                    self.loggin.emit(
                        f'Error moviendo archivo: {split(opth)[1]}<br>{str(e)}', LogLevel.ERROR.value)

        self.loggin.emit("Mover finalizado.", LogLevel.DEBUG.value)
        # re-generate list, this signal trigger the gen_list slot
        # call directly from thread can crash qt and also create throw
        # QObject::connect: Cannot queue arguments of type 'QVector<int>'
        self.moveGroup.buttonClicked.emit(self.moverRadio)
