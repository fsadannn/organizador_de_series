import os
from typing import List, Tuple

import qtawesome as qta
from fs.errors import DirectoryExpected
from fs.info import Info
from fs.osfs import OSFS
from fs.path import join
from fs.wrap import read_only
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from . import ui as UIs
from .series_renamer.renamer import ChapterMetadata
from .utils.formats import is_video
from .utils.qt_utils import Logger, LogLevel
from .utils.rename import rename
from .utils.resource_loader import get_as_file_like_string
from .utils.sync import ChaptersRange, SerieFS


class Falta(QWidget):
    logginn = pyqtSignal(str, str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loggin = Logger('Falta', self.logginn)
        self.caps_list: SerieFS = SerieFS()
        self._text: str = ''

        ui_file = get_as_file_like_string(UIs, 'falta.ui')
        uic.loadUi(ui_file, self)

        folderIcon = qta.icon(
            'fa5s.folder-open',
            color='orange',
            color_active='red')
        btn: QPushButton = self.pathbtn
        btn.setText('')
        btn.setIcon(folderIcon)

        findIcon = qta.icon(
            'fa5s.search',
            color='orange',
            color_active='red')
        btn: QPushButton = self.findButton
        btn.setText('')
        btn.setIcon(findIcon)

        saveIcon = qta.icon(
            'fa5s.save',
            color='black',
            color_active='red')
        btn: QPushButton = self.saveButton
        btn.setText('')
        btn.setIcon(saveIcon)

        self.faltaGroup = QButtonGroup()
        self.faltaGroup.addButton(self.faltaRadio, 1)
        self.faltaGroup.addButton(self.ultimoRadio, 2)
        self.faltaGroup.setExclusive(True)

        li: QTreeWidget = self.treeWidget
        li.headerItem().setText(0, '')

        li.itemExpanded.connect(self.change_open_icon)
        li.itemCollapsed.connect(self.change_close_icon)
        li.itemDoubleClicked.connect(self.open_folder)
        self.pathbtn.clicked.connect(self.set_path)
        self.findButton.clicked.connect(self.proccess)
        self.saveButton.clicked.connect(self.save_text)

    @pyqtSlot(QTreeWidgetItem, int)
    def open_folder(self, item: QTreeWidgetItem, column: int):
        if item.childCount() == 0:
            return

        if self.pathbar.text() == '':
            return

        base = self.pathbar.text()
        os.startfile(os.path.join(base, item.text(column)))

    @pyqtSlot()
    def save_text(self):
        #print('saving', self.falta_txt)
        if self.pathbar.text() == '':
            return

        name: str = 'falta.txt' if self.faltaGroup.checkedId() == 1 else 'último.txt'

        path = os.path.join(self.pathbar.text(), name)

        with open(path, 'w') as f:
            f.write(self._text)

        self.loggin.emit(f'Guardado: {path}', LogLevel.INFORMATION.value)

    @pyqtSlot(QTreeWidgetItem)
    def change_open_icon(self, item: QTreeWidgetItem):
        folderIcon = qta.icon(
            'fa5s.folder-open',
            color='orange')
        item.setIcon(0, folderIcon)

    @pyqtSlot(QTreeWidgetItem)
    def change_close_icon(self, item: QTreeWidgetItem):
        folderIcon = qta.icon(
            'fa5s.folder',
            color='orange')
        item.setIcon(0, folderIcon)

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
        dirr: str = self._get_path()

        if dirr is None or dirr == '':
            return

        self.pathbar.setText(dirr)

    def _get_caps(self):
        base = self.pathbar.text()
        with read_only(OSFS(base)) as ff:
            proces: List[Tuple[Info, Info]] = []
            folders_: List[Info] = []

            for i in ff.scandir('/'):
                if i.is_dir:
                    folders_.append(i)

            for i in folders_:
                path = join('/', i.name)

                try:
                    for j in ff.scandir(path):
                        if j.is_file and is_video(j.name):
                            proces.append((j, i))
                except (PermissionError, DirectoryExpected) as e:
                    self.loggin.emit("Acceso denegado a" +
                                     join(base, i.name), LogLevel.ERROR.value)

            folders: SerieFS = SerieFS()
            for filee, fold in proces:
                folder_name = fold.name
                file_name = filee.name
                self.loggin.emit("Procesando: " + join(base,
                                                       folder_name, file_name), LogLevel.INFORMATION.value)

                serie: ChapterMetadata = rename(file_name)

                if not serie.episode:
                    continue

                folders.add_serie_episode(
                    folder_name, serie.serie_name, serie.episode)

            self.caps_list = folders

    @pyqtSlot()
    def proccess(self):
        if self.pathbar.text() == '':
            return

        folderIcon = qta.icon(
            'fa5s.folder',
            color='orange')
        videoIcon = qta.icon(
            'fa5s.file-video',
            color='blue')
        li: QTreeWidget = self.treeWidget
        li.clear()
        li.headerItem().setText(0, self.pathbar.text())

        self._get_caps()
        caps_list: SerieFS = self.caps_list

        if self.faltaGroup.checkedId() == 1:
            falta_txt = ''

            for i in sorted(caps_list.keys()):
                parent: QTreeWidgetItem = QTreeWidgetItem()
                parent.setIcon(0, folderIcon)
                parent.setText(0, i)
                should_add_parent: bool = False

                for k in sorted(caps_list[i].keys()):
                    lost_chapters: List[ChaptersRange] = caps_list[i].compute_lost_chapters(
                        k)

                    if len(lost_chapters) == 0:
                        continue

                    should_add_parent = True

                    falta_txt += f'{k}: '

                    for n, j in enumerate(lost_chapters):
                        if n != 0:
                            falta_txt += ', '

                        falta_txt += j.as_text()

                        child = QTreeWidgetItem(parent)
                        child.setIcon(0, videoIcon)
                        child.setText(0, f'{k}: {j.as_text()}')
                        parent.addChild(child)

                    falta_txt += '\n'

                if should_add_parent:
                    li.addTopLevelItem(parent)
                    parent.setExpanded(True)
                else:
                    del parent

            self._text = falta_txt
        elif self.faltaGroup.checkedId() == 2:
            last_txt = ''

            for i in sorted(caps_list.keys()):
                parent: QTreeWidgetItem = QTreeWidgetItem()
                parent.setIcon(0, folderIcon)
                parent.setText(0, i)

                for k in sorted(caps_list[i].keys()):
                    txt = f'{k} - {caps_list[i].last(k)}'
                    last_txt += txt + '\n'
                    child: QTreeWidgetItem = QTreeWidgetItem(parent)
                    child.setIcon(0, videoIcon)
                    child.setText(0, txt)
                    parent.addChild(child)

                li.addTopLevelItem(parent)
                parent.setExpanded(True)

            self._text = last_txt
