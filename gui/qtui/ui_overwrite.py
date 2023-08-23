from PyQt5 import QtWidgets
from PyQt5.QtGui import QDesktopServices


class DesktopTextBrowser(QtWidgets.QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(True)
        self.anchorClicked.connect(self.handle_anchor_clicked)

    @staticmethod
    def handle_anchor_clicked(url):
        QDesktopServices.openUrl(url)
