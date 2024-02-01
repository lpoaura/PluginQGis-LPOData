"""Fake news"""

from qgis.gui import QgsMessageBar
from PyQt5.QtWidgets import QDialog, QSizePolicy, QLabel, QDialogButtonBox, QVBoxLayout

class JokeDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.setWindowTitle("BLAGOUNETTE")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        message = QLabel(" Vous y avez vraiment cru !? ;)")
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonbox.accepted.connect(self.close)
        self.layout().addWidget(message)
        self.layout().addWidget(self.buttonbox)
        self.layout().addWidget(self.bar)

jokeDialog = JokeDialog()
jokeDialog.show()