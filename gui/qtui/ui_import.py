from . import main_ui

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget


class MainUI(main_ui.Ui_MainWindow, QWidget):
    def __init__(self):
        super(MainUI, self).__init__()

    def setupUi(self, MainWindow):
        super(MainUI, self).setupUi(MainWindow)
        # MainWindow.setFixedSize(MainWindow.rect().width(), MainWindow.rect().height())

    def show_messagebox(self, title, text, bts=QtWidgets.QMessageBox.Yes):
        QtWidgets.QMessageBox.information(self, title, text, bts)


