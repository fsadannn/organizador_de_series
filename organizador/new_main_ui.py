from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QTextEdit

from . import ui as UIs
from .new_renombrar import Renombrar
from .utils.qt_utils import LogLevel, logcolor
from .utils.resource_loader import get_as_file_like_string


class Ui(QMainWindow):
    def __init__(self):
        super().__init__()  # Call the inherited classes __init__ method
        ui_file = get_as_file_like_string(UIs, 'main.ui')
        uic.loadUi(ui_file, self)  # Load the .ui file
        self.show()  # Show the GUI
        self.renombrar = Renombrar(self)
        tabw: QTabWidget = self.tabWidget
        tabw.addTab(self.renombrar, 'Mover/Renombrar')

        self.renombrar.logginn.connect(self.loggin)

    @pyqtSlot(str, str, int)
    def loggin(self, name: str, txt: str, level: int):
        logger: QTextEdit = self.logger

        if logger.document().lineCount() > 1000:
            logger.clear()

        txtt = logcolor(name + ': ', LogLevel.NAME.value)
        txtt += logcolor(txt, level)
        logger.append(txtt)
