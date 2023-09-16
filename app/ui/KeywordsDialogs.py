import sys
import time
import copy
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from app.packages.atwoodtypes import *

class KeywordsDialogs(QDialog):

	def __init__(self, parent=None, keywords=[]):
		super(KeywordsDialogs, self).__init__(parent)

		self.parent = parent
		#super(MassWriter, self).__init__() #provicional hasta que vea por que hay un problema de visualizacion

		self.configureWindow()
		self.createAttributes(keywords)
		self.createLayout()
		#self.createMenuBar() #desactivado hasta que implemente las funciones
		self.createKeywordsList()
		self.createSendButton()	
		self.createCancelButton()

	def warningMessage(self, message):
		message_box = QMessageBox()
		message_box.setIcon(QMessageBox.Warning)
		message_box.setText(message)
		message_box.setWindowTitle("Advertencia")
		message_box.setStandardButtons(QMessageBox.Ok)
		message_box.exec_()

	def configureWindow(self):
		self.setWindowTitle('Escritura masiva')
		self.setFixedSize(480, 480)

	def createAttributes(self, keywords):
		self.keywords = keywords

	def createLayout(self):
		self.layout = QGridLayout()
		self.setLayout(self.layout)

	def createKeywordsList(self):
		self.keywordsListLabel = QLabel()
		self.keywordsListLabel.setText('Introduce una lista de títulos o frases clave (uno por línea):')
		self.keywordsList = QPlainTextEdit()
		self.keywordsList.textChanged.connect(self.updateKeywords)

		if len(self.keywords):
			for keyword in self.keywords:
				self.keywordsList.insertPlainText(keyword.strip() + '\n')

		if not len(self.keywordsList.toPlainText()):
			self.keywordsList.setPlaceholderText('Qué es ChatGPT\nTodo sobre la IA generativa\n¿Cómo usar la API de OpenAI?')

		self.layout.addWidget(self.keywordsListLabel, 0, 0, 1, 2)
		self.layout.addWidget(self.keywordsList, 1, 0, 1, 2)

	def createSendButton(self):
		self.sendButton = QPushButton()
		self.sendButton.setText('¡Comenzar!')
		self.sendButton.clicked.connect(self.recollect)
		self.layout.addWidget(self.sendButton, 2, 0, 1, 1)

	def createCancelButton(self):
		self.cancelButton = QPushButton()
		self.cancelButton.setText('Cancelar')
		self.cancelButton.clicked.connect(self.close)
		self.layout.addWidget(self.cancelButton, 2, 1, 1, 1)

	def removeLastDot(self, text):

		while text.endswith('.'): 
			text = text[:-1] 

		return text

	def updateKeywords(self):
		print("FUNC: updateKeywords() ->", end=' ')
		self.keywords = self.keywordsList.toPlainText().strip().splitlines()
		tmp = []
		for keyword in self.keywords:
			tmp.append(keyword.strip())
		self.keywords = tmp

	def recollect(self):
		print("FUNC: recollect() ->", end=' ')

		keywords = self.keywordsList.toPlainText().strip().splitlines()
		n = len(keywords)

		if n < 2:
			self.warningMessage('¡Introduce al menos dos títulos o frases clave!')
			return

		self.keywords = []

		for keyword in keywords:
			self.keywords.append(keyword.strip())

		self.accept()

	def getKeywords(self):
		print("FUNC: getKeywords() ->", end=' ')
		return self.keywords