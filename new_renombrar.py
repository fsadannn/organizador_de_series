import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtWidgets import QPushButton, QWidget


class Renombrar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi('renombrar.ui', self)

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
        btn: QPushButton = self.selectAll
        btn.setText('')
        btn.setIcon(selallIcon)

        selinvIcon = qta.icon(
            'mdi.select-inverse',
            color='blue',
            color_active='red')
        btn: QPushButton = self.selectInvert
        btn.setText('')
        btn.setIcon(selinvIcon)

        procIcon = qta.icon(
            'mdi.play',
            color='green',
            color_active='red')

        btn: QPushButton = self.proc
        btn.setText('')
        btn.setIcon(procIcon)
