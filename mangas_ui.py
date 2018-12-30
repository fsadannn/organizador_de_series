# -*- coding: UTF-8 -*-
#!/usr/bin python3
# @author: SadanNN
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QTextEdit, QDockWidget
from PyQt5.QtCore import Qt
from mvrename import MoveRename
from utils import logcolor


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        self.cw1 = MoveRename()
        self.setCentralWidget(self.cw1)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logsdock = QDockWidget("Logs", self)
        self.logsdock.setAllowedAreas(Qt.BottomDockWidgetArea|Qt.TopDockWidgetArea)
        self.logsdock.setWidget(self.logs)
        self.logsdock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logsdock)
        self.cw1.loggin.connect(self.loggin)

    def loggin(self, txt, level):
        if self.logs.document().lineCount() > 1000:
            self.logs.clear()
        txt = logcolor(txt, level)
        self.logs.append(txt)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Main()
    w.show()
    w.resize(784, 521)
    sys.exit(app.exec_())
