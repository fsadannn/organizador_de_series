from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QTextEdit

from . import ui as UIs
from .falta import Falta
from .new_renombrar import Renombrar
from .utils.qt_utils import LogLevel, logcolor
from .utils.resource_loader import get_as_file_like_string


class Ui(QMainWindow):
    def __init__(self):
        super().__init__()  # Call the inherited classes __init__ method
        ui_file = get_as_file_like_string(UIs, 'main.ui')
        uic.loadUi(ui_file, self)  # Load the .ui file

        tabw: QTabWidget = self.tabWidget

        self.renombrar = Renombrar(self)
        tabw.addTab(self.renombrar, 'Mover/Renombrar')

        self.falta = Falta(self)
        tabw.addTab(self.falta, 'Falta')

        self.renombrar.logginn.connect(self.loggin)
        self.falta.logginn.connect(self.loggin)
        self.show()  # Show the GUI

    @pyqtSlot(str, str, int)
    def loggin(self, name: str, txt: str, level: int):
        logger: QTextEdit = self.logger

        if logger.document().lineCount() > 1000:
            logger.clear()

        txtt = logcolor(name + ': ', LogLevel.NAME.value)
        txtt += logcolor(txt, level)
        logger.append(txtt)
