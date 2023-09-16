import sys
import time
import copy
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from atwoodtypes import *

class AutolinkDialog(QDialog):

	def __init__(self, parent=None):
		super(AutolinkDialog, self).__init__(parent)

		self.parent = parent
		self.articles = self.parent.articles

		self.configureWindow()
		self.createAttributes()
		self.createLayout()

	def configureWindow(self):
		self.setWindowTitle('Seleccionar artículo')
		#self.setFixedSize(480, 480)

	def createAttributes(self, keywords):
		pass

	def createLayout(self):
		self.layout = QGridLayout()
		self.setLayout(self.layout)