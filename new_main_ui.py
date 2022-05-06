import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget

from new_renombrar import Renombrar


class Ui(QMainWindow):
    def __init__(self):
        super().__init__()  # Call the inherited classes __init__ method
        uic.loadUi('main.ui', self)  # Load the .ui file
        self.show()  # Show the GUI
        self.renombrar = Renombrar(self)
        tabw: QTabWidget = self.tabWidget
        tabw.addTab(self.renombrar, 'Mover/Renombrar')


app = QApplication(sys.argv)  # Create an instance of QtWidgets.QApplication
app.setStyle('Fusion')
window = Ui()  # Create an instance of our class
app.exec_()  # Start the application
