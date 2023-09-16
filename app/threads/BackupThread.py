import time
import copy
import openai
import json
import sys
import os
import app.packages.myutils as mu
import markdown as md
from colorama import Fore
from PyQt5.QtCore import QVariant, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCursor
from app.packages.atengine.atwriter import AtWriter
from app.packages.autolink2 import Autolink


class BackupThread(QThread):
	backup = pyqtSignal()

	def __init__(self, parent):
		super(BackupThread, self).__init__(parent)

	@pyqtSlot()
	def run(self):
		while True:
			time.sleep(10)
			self.backup.emit()	
