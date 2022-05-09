from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .version import version


class About(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cl: QVBoxLayout = QVBoxLayout(self)
        self.cl.setAlignment(Qt.AlignHCenter)

        self.setFont(QFont('', 8))

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.name = QLabel(f'Organizador de Series {version}', self)
        self.name.setFixedHeight(30)
        tt.addWidget(self.name)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.cp = QLabel('Copyright © 2022 Frank S. Naranjo', self)
        self.cp.setFixedHeight(30)
        tt.addWidget(self.cp)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.cp = QLabel(
            '<a href="https://github.com/fsadannn/organizador_de_series">https://github.com/fsadannn/organizador_de_series</a>', self)
        self.cp.setTextFormat(Qt.RichText)
        self.cp.setFixedHeight(30)
        self.cp.setOpenExternalLinks(True)
        tt.addWidget(self.cp)
        self.cl.addLayout(tt)

        self.setLayout(self.cl)
