import sys
import time
import copy
import re
import os
import json
from threading import Thread
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from app.packages.atengine.atchat import AtChat

class Sumarize(QThread):
	summary = pyqtSignal(str)
	error = pyqtSignal(str)

	def __init__(self, parent):
		super(Sumarize, self).__init__(parent)
		self.parent = parent

	@pyqtSlot(str)
	def run(self):
		while self.parent.isVisible():
			chat = self.parent.chatBox.toPlainText()
			limit = 150 if len(chat) > 150 else len(chat)
			chatStart = chat[0:limit]
			command = '''
	Sigue estrictamente mis instrucciones. Resume el tema del siguiente fragmento de conversación en una frase breve:

	"%s".

	Quiero que tu respuesta tenga estrictamente el siguiente formato: "#TEMA: tema".
			''' % chatStart
			atc = AtChat(self.parent.apikey)
			atc.temperature = 0
			atc.topP = 0
			atc.frequencyPenalty = 0
			atc.presencePenalty = 0

			try:
				answer = atc.answer(command)
			except Exception as e:
				self.error.emit(str(e))
				self.summary.emit('')
				return

			answer = answer.split(':')[1].strip()
			answer = re.sub(r"\.$", "", answer) 
			self.summary.emit(answer)
			#print(f'Sumario creado: {answer}.')
			time.sleep(10)


class ChatGPT(QWidget):

	def __init__(self, parent=None):
		super(ChatGPT, self).__init__(parent)

		self.apikey = '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'

		self.configureWindow()
		self.createAttributes()
		self.createLayout()
		self.createMenuBar() #desactivado hasta que implemente las funciones
		self.createChatBox()
		self.createInputBox()
		self.createSendButton()	
		self.createCancelButton()

		self.inputBox.setFocus()
		self.keyPressEvent = self.shortcut

		self.chatBox.insertHtml('<b>AT:</b> ¡Hola!<br>')

	def showEvent(self, e):
		self.startSummarizer()

	def configureWindow(self):
		self.setFixedSize(480, 270)
		self.setWindowTitle('¡Chat AT!')
		self.setWindowIcon(QIcon('muelagpt.png'))

	def createAttributes(self):
		self.chatbot = AtChat(self.apikey)
		self.chatbot.setModel('gpt-3.5-turbo-16k')
		#print('Ejecutándose con %s.' % self.chatbot.model)
		self.answer = ''
		self.dots = -1
		self.cancelled = False
		self.answerThread = Thread()
		self.summary = 'Saludo del chatbot.'

	def createLayout(self):
		self.layout = QGridLayout()
		self.setLayout(self.layout)

	def createMenuBar(self):
		self.menuBar = QMenuBar()
		self.fileMenu = self.menuBar.addMenu('Archivo')
		self.helpMenu = self.menuBar.addMenu('Ayuda')

		openAction = QAction(QIcon(), 'Abrir', self)
		openAction.triggered.connect(self.openChat)
		saveAction = QAction(QIcon(), 'Guardar', self)
		saveAction.triggered.connect(self.saveChat)
		apiAction = QAction(QIcon(), 'Clave de la API')
		apiAction.triggered.connect(self.setAPIkey)
		aboutAction = QAction(QIcon(), 'Acerca de...', self)
		aboutAction.triggered.connect(self.about)

		self.fileMenu.addAction(openAction)
		self.fileMenu.addAction(saveAction)
		self.helpMenu.addAction(apiAction)
		self.helpMenu.addAction(aboutAction)

		self.layout.addWidget(self.menuBar, 0, 0, 1, 5)

	def createChatBox(self):
		self.chatBox = QTextEdit()
		self.chatBox.setReadOnly(True)
		self.chatBox.setStyleSheet('QTextEdit:disabled {background-color:white;color:black}')
		#self.chatBox.cursorPositionChanged.connect(self.moveCursorToEnd)
		self.layout.addWidget(self.chatBox, 1, 0, 1, 5)
		self.layout.setRowStretch(0, 10)

	def createInputBox(self):
		self.inputBox = QTextEdit()
		self.inputBox.setMaximumSize(QSize(10000, 50))
		self.inputBox.cursorPositionChanged.connect(self.setButtonState)
		#self.keyPressEvent = self.checkForSend
		self.layout.addWidget(self.inputBox, 2, 0, 2, 4)

	def createSendButton(self):
		self.sendButton = QPushButton()
		self.sendButton.setText('Enviar')
		self.sendButton.setEnabled(False)
		self.sendButton.clicked.connect(self.prompt)
		self.layout.addWidget(self.sendButton, 2, 4, 1, 1)

	def createCancelButton(self):
		self.cancelButton = QPushButton()
		self.cancelButton.setText('Cancelar')
		self.cancelButton.setEnabled(False)
		self.cancelButton.clicked.connect(self.cancel)
		self.layout.addWidget(self.cancelButton, 3, 4, 1, 1)

	def startSummarizer(self):
		self.sumarizer = Sumarize(self)
		self.sumarizer.summary[str].connect(self.setSummary)
		self.sumarizer.error[str].connect(self.errorActions)
		self.sumarizer.start()

	def setSummary(self,summary):
		if len(summary):
			self.summary = summary

	def resetChatbot(self):
		cloneChatbot = copy.deepcopy(self.chatbot)
		self.chatbot = cloneChatbot

	def shortcut(self, e):
		content = self.inputBox.toPlainText().strip()
		if e.key() == Qt.Key_Escape and self.answerThread.is_alive():
			self.cancel()
		elif e.key() == Qt.Key_Insert and len(content):
			self.prompt()

	def setButtonState(self):
		content = self.inputBox.toPlainText().strip()

		if not len(content):
			self.sendButton.setEnabled(False)
		else:
			self.sendButton.setEnabled(True)

	def moveCursorToEnd(self, e=None):
		self.chatBox.moveCursor(QTextCursor.End)

	def openChat(self):
		
		file_path = QFileDialog.getOpenFileName(self,'Abrir Archivo','chats','Chat Files (*.chat)')[0]
    
		if file_path:
			with open(file_path, 'r') as f:
				data = json.load(f)
				self.chatBox.setHtml(data['text'])

	def saveChat(self):

		filename = os.path.join('chats', self.summary)
		file_path = QFileDialog.getSaveFileName(self,'Guardar Archivo', filename,'Chat Files (*.chat)')[0]
    	
		if file_path:
			print(file_path)
			data = {"text" : self.chatBox.toHtml()}
			if file_path.rfind('.chat') == -1:
				file_path = file_path + '.chat'
			print(file_path)

			with open(file_path,'w') as f:
				json.dump(data,f)

	def about(self):
		pass

	def setAPIkey(self):
		pass

	def chat(self, prompt):
		self.moveCursorToEnd()

		try:
			self.answer = self.chatbot.answer(prompt)
		except Exception as e:
			self.errorActions(e)

	def cancel(self):
		self.cancelled = True
		self.answerThread = Thread()
		self.resetChatbot()
		self.removeGptLine()
		self.answer = ''
		self.cancelButton.setEnabled(True)
		self.chatBox.ensureCursorVisible()
		self.inputBox.setReadOnly(False)
		self.chatBox.setEnabled(True)
		self.inputBox.setFocus()

	def stopByError(self):
		self.cancelled = True
		self.answerThread = Thread()
		self.resetChatbot()
		self.errorActions()
		self.answer = ''
		self.cancelButton.setEnabled(True)
		self.chatBox.ensureCursorVisible()
		self.inputBox.setReadOnly(False)
		self.chatBox.setEnabled(True)
		self.inputBox.setFocus()

	def errorActions(self, e):
		cursor = self.chatBox.textCursor()
		cursor.movePosition(QTextCursor.Down)
		cursor.select(QTextCursor.LineUnderCursor)
		cursor.removeSelectedText()
		#cursor.insertHtml('<b>Yo</b>: ')
		cursor = self.chatBox.textCursor()
		cursor.movePosition(QTextCursor.Down)
		cursor.select(QTextCursor.LineUnderCursor)
		cursor.removeSelectedText()
		self.chatBox.insertHtml('<i style="color:red">Error de AT: %s</i><br>' % e)

	def writeAnswer(self):
		answer = self.answer.replace('<br>', '\n').replace('&nbsp', ' ').replace('```', '') + '\n'
		self.chatBox.insertPlainText(answer)	

	def checkIfDone(self):
		if self.answerThread.is_alive():
			if not self.cancelled:
				self.waitingMessage()
				QTimer.singleShot(100, self.checkIfDone)
		else:
			if not self.cancelled:
				self.removeDots()
				self.writeAnswer()
				self.chatBox.ensureCursorVisible()
				self.answer = ''
				self.inputBox.setReadOnly(False)
				self.chatBox.setEnabled(True)
				self.cancelButton.setEnabled(True)
				self.inputBox.setFocus()

	def removeDots(self):
		cursor = self.chatBox.textCursor()
		cursor.movePosition(QTextCursor.Down)
		cursor.select(QTextCursor.LineUnderCursor)
		cursor.removeSelectedText()
		cursor.insertHtml('<b>AT</b>: ')

	def removeGptLine(self):
		cursor = self.chatBox.textCursor()
		cursor.movePosition(QTextCursor.Down)
		cursor.select(QTextCursor.LineUnderCursor)
		cursor.removeSelectedText()
		#cursor.insertHtml('<b>Yo</b>: ')
		cursor = self.chatBox.textCursor()
		cursor.movePosition(QTextCursor.Down)
		cursor.select(QTextCursor.LineUnderCursor)
		cursor.removeSelectedText()
		self.chatBox.insertHtml('<i style="color:gray">Respuesta cancelada</i><br>')

	def waitingMessage(self):

		self.removeDots()
		message = '<i>%s</i>' % '.' * self.dots
		
		if self.dots >= 3:
			self.dots = -1	

		self.chatBox.insertHtml(message)
		self.chatBox.ensureCursorVisible()
		self.dots = self.dots + 1

	def prompt(self):
		self.cancelled = False
		prompt = self.inputBox.toPlainText().strip()
		#prompt = prompt.replace('\n', '<br>')
		self.inputBox.clear()
		self.moveCursorToEnd()
		self.chatBox.insertHtml('<strong>Yo:</strong> ')
		self.chatBox.insertPlainText(prompt)
		self.chatBox.insertHtml('<br><b>AT:</b>')
		self.chatBox.ensureCursorVisible()
		self.inputBox.setReadOnly(True)
		self.chatBox.setEnabled(False)
		self.cancelButton.setEnabled(True)
		self.moveCursorToEnd()
	
		self.answerThread = Thread(target=self.chat, args=[prompt])
		self.answerThread.start()
		QTimer.singleShot(100, self.checkIfDone)
		

if __name__ == '__main__':
	app = QApplication(sys.argv)
	chatGPT = ChatGPT()
	chatGPT.show()
	sys.exit(app.exec_())
		