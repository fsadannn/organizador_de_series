# -*- coding: UTF-8 -*-
# !/usr/bin python3
# @author: SadanNN
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTextEdit, QDockWidget, QTabWidget
from PyQt5.QtCore import Qt, QByteArray, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from move_rename import MoveRename
from falta import Falta
from ftp_manager import FTPGui
from file_sync import FileGui
from utils import logcolor
from appicon import icon
from utils import NAME

class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        self.tabw = QTabWidget(self)

        self.cw1 = MoveRename()
        self.tabw.addTab(self.cw1,'Mover/Renombrar')

        self.cw2 = Falta()
        self.tabw.addTab(self.cw2,'Falta')

        self.cw3 = FTPGui()
        self.tabw.addTab(self.cw3,'FTP')

        self.cw4 = FileGui()
        self.tabw.addTab(self.cw4,'File')

        self.tabw.setTabShape(QTabWidget.Triangular)
        self.tabw.setTabPosition(QTabWidget.West)
        self.setCentralWidget(self.tabw)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logsdock = QDockWidget("Logs", self)
        self.logsdock.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.logsdock.setWidget(self.logs)
        self.logsdock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logsdock)
        self.cw1.logginn.connect(self.loggin)
        self.cw2.logginn.connect(self.loggin)
        self.cw3.logginn.connect(self.loggin)
        self.cw4.logginn.connect(self.loggin)

    @pyqtSlot(str, str, int)
    def loggin(self, name, txt, level):
        if self.logs.document().lineCount() > 1000:
            self.logs.clear()
        txtt = logcolor(name+': ', NAME)
        txtt += logcolor(txt, level)
        self.logs.append(txtt)


#if __name__ == '__main__':

app = QApplication(sys.argv)
app.setStyle('Fusion')
w = Main()
ic, ext=icon()
qtimgd = QByteArray(ic)
px = QPixmap()
px.loadFromData(qtimgd, ext)
app.setWindowIcon(QIcon(px))
w.resize(784, 521)
w.show()
sys.exit(app.exec_())
