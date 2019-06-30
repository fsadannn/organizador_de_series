# -*- coding: UTF-8 -*-
# !/usr/bin python3
# @author: SadanNN
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTextEdit, QDockWidget, QTabWidget
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QPixmap, QIcon
from move_rename import MoveRename
from falta import Falta
from ftp_manager import FTPGui
from utils import logcolor
from appicon import icon

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
        self.cw1.loggin.connect(self.loggin)
        self.cw2.loggin.connect(self.loggin)
        self.cw3.loggin.connect(self.loggin)

    def loggin(self, txt, level):
        if self.logs.document().lineCount() > 1000:
            self.logs.clear()
        txt = logcolor(txt, level)
        self.logs.append(txt)


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
