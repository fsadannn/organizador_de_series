# -*- coding: UTF-8 -*-
# !/usr/bin python3
# @author: SadanNN

import sys

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication

import organizador.assets as Assets
from organizador.new_main_ui import Ui
from organizador.utils.resource_loader import get_as_bytes

app = QApplication(sys.argv)  # Create an instance of QtWidgets.QApplication
app.setStyle('Fusion')
iconData = get_as_bytes(Assets, 'icon.ico')
px = QPixmap()
px.loadFromData(iconData, 'ico')
app.setWindowIcon(QIcon(px))
window = Ui()  # Create an instance of our class
app.exec_()  # Start the application
