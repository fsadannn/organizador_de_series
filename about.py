from typing import Text

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from version import version


class About(QWidget):
    def __init__(self):
        super(About, self).__init__()
        self.cl: QVBoxLayout = QVBoxLayout(self)
        self.cl.setAlignment(Qt.AlignHCenter)

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.name = QLabel(f'Organizador de Series {version}', self)
        self.name.setFixedHeight(20)
        tt.addWidget(self.name)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.cp = QLabel('Copyright © 2021 Frank S. Naranjo', self)
        self.cp.setFixedHeight(20)
        tt.addWidget(self.cp)
        self.cl.addLayout(tt)

        tt = QHBoxLayout()
        tt.setAlignment(Qt.AlignHCenter)
        self.cp = QLabel(
            '<a href="https://github.com/fsadannn/organizador_de_series">https://github.com/fsadannn/organizador_de_series</a>', self)
        self.cp.setTextFormat(Qt.RichText)
        self.cp.setFixedHeight(20)
        self.cp.setOpenExternalLinks(True)
        tt.addWidget(self.cp)
        self.cl.addLayout(tt)

        obj = self.cl
        print(obj.geometry().x(), obj.geometry().y(),
              obj.geometry().width(), obj.geometry().height())

        self.setLayout(self.cl)
