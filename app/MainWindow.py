version = '1.1'
fast_testing_mode = False

config_file = "atwood.conf"
apikey_file = './secret/api.key'
media_directory = 'media'
default_doc_directory = 'storage/documents'
default_preset_directory = 'storage/presets'

doc_ext = ('atw', 'Documentos de Atwood (*.atw)')
export_exts = [
	('docx', 'Documentos de Word (*.docx)'),
	('odt', 'Documentos de Writer (*.dot)'), 
	('html', 'Páginas web (*.html)' )
	]
pst_ext = ('pst', 'Archivo de preset (*.pst)')
default_doc_name = 'Documento sin título'

# GLOBAL

import sys
import time
import os
import json
import openai
import markdown as md
from colorama import Fore

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# PACKAGES

import app.packages.secret as secret
import app.packages.myutils as mu
from app.packages.myutils import printerr as printerr
from app.packages.myutils import printwarn as printwarn
from app.packages.atengine.atwriter import *
from app.packages.atwoodtypes import *

# DIALOGS

from app.ui.ConfDialog import ConfDialog
from app.ui.ChatGPT import ChatGPT
from app.ui.KeywordsDialogs import KeywordsDialogs
from app.ui.RetryDialog import RetryDialog

#Threads

from app.threads.ArticleThread import ArticleThread
from app.threads.AutolinkThread import AutolinkThread
from app.threads.BackupThread import BackupThread
from app.threads.FinalizeTasksThread import FinalizeTasksThread
from app.threads.IndexThread import IndexThread
from app.threads.MessageLoopThread import MessageLoopThread
from app.threads.PrepBatchThread import PrepBatchThread


class MainWindow(QWidget):

	def __init__(self, parent = None, width=1280, height=720):

		super(MainWindow, self).__init__()

		self.width = width
		self.height = height

		self.initialize()
		self.configureWindow()	
		self.createMainLayout()

		#CREATE DIALOGS
		self.chatbot = ChatGPT()
		self.infoMessageDialog = QMessageBox()
		self.warningMessageDialog = QMessageBox()
		self.askMessageDialog = QMessageBox()
		self.errorMessageDialog = QMessageBox()
		self.confDialog = ConfDialog()

		#CREATE WIDGETS
		self.createMenuBar()
		self.createTopicWidgets()
		self.createAuthorWidgets()
		self.createStyleWidgets()
		self.createReaderWidgets()
		self.createInstructionsWidgets()
		self.createIndexWidgets()
		self.createSuggestIndexButton()
		self.createWriteButton()
		self.createCancelButton()
		self.createEditorTextEdit()
		self.createStatusBar()
		self.createMetaCheckbox()
		self.createAutointroCheckbox()
		self.createAutolinkCheckbox()
		self.createShowTitleCheckbox()

		QTimer.singleShot(100, self.finalConstructorTasks)

	#################################################################################################
	### INITIALIZATION METHODS ###
	#################################################################################################
	def lookFor(self, path):
		if not os.path.exists(path):
			os.makedirs(path)

	def loadWritingConfig(self):
		try:
			with open(config_file, "r") as file:
				values = json.load(file)
		except FileNotFoundError:
			printerr("ERROR: ", "No se encuentra el archivo de configuración '%s'" % config_file )
			return
		except json.JSONDecodeError:
			printerr("ERROR", "Formato JSON inválido en el archivo de configuración.")
			return

		self.conf = values
		print(json.dumps(self.conf, indent=4))
		
	def initialize(self):

		self.conf = None
		self.currWriter = None
		self.unfinishedArtWriter = None
		self.unfinishedArtData = None
		self.err = False
		self.cdots = 1
		self.cancelled = False
		self.fileSaved = False
		self.indexProgress = []	
		self.docName = default_doc_name
		self.docsFolder = default_doc_directory
		self.presetsFolder = default_preset_directory
		self.lookFor(self.docsFolder)
		self.lookFor(self.presetsFolder)
		self.filename = os.path.join(os.getcwd(), self.docsFolder, self.docName)
		self.expFileName = os.path.join(os.getcwd(), self.docsFolder, self.docName)
		self.expExt = 'docx'
		self.writer = None
		self.writingThread = None
		self.messageThread = None
		self.indexWriter = None
		self.indexThread = None
		self.suggestedIndex = ''
		self.keywords = []
		self.batchDataIndex = []
		self.prepBatchThread = None
		self.autolinkThread = None
		self.interactionBlocked = False
		self.writingMode = 'article'

		self.finalizeTasksThread = FinalizeTasksThread(self)
		self.finalizeTasksThread.removeMsg.connect(self.removeMessage)
		self.finalizeTasksThread.finished.connect(self.postActivityTasks)

	def finalConstructorTasks(self):
		#self.readAtwFile(os.path.join(self.docsFolder, 'default.%s' % doc_ext[0]))
		self.topicLineEdit.setPlaceholderText('Qué es ChatGPT')
		self.authorLineEdit.setPlaceholderText('Elon Musk')
		self.styleTextEdit.setPlaceholderText('Sarcástico y arrogante')
		self.topicLineEdit.setPlaceholderText('Qué es ChatGPT')
		self.readerTextEdit.setPlaceholderText('Público latinoamericano')
		self.instructionsTextEdit.setPlaceholderText('Tutea al lector')
		self.indexTextEdit.setPlaceholderText('Qué es\nPara qué sirve\nFuturo\nConclusiones')

		self.mistery = 'ep-k9CZ0JPRWKgiz1xil0jZNkls5SIuR87XgNN6ZuN4=' #clave para guardar y leer la API key de OpenAI
		self.apikey = self.getAPIKey(first = True)
		self.backupThread = BackupThread(self)
		self.backupThread.backup.connect(self.backupAtwFile)
		self.backupThread.start()

		self.loadWritingConfig()
		self.updateGUI()

	#################################################################################################
	### WIDGETS CREATION METHODS ###
	#################################################################################################

	def configureWindow(self):
		self.setGeometry(0, 0, self.width, self.height)
		self.resize(self.width, self.height)
		self.setWindowIcon(QIcon('logo.png'))
		self.setWindowTitle('Atwood %s' % version)

	def createMainLayout(self):
		self.mainLayout = QGridLayout()
		self.setLayout(self.mainLayout)

	def createMenuBar(self):
		self.menuBar = QMenuBar()
		self.mainLayout.addWidget(self.menuBar, 0, 0, 1, 10)

		self.newFileItem = QAction(QIcon(), '&Nuevo', self)
		self.newFileItem.triggered.connect(self.newFile)

		self.openFileItem = QAction(QIcon(), '&Abrir', self)
		self.openFileItem.triggered.connect(self.openFile)

		self.saveFileAsItem = QAction(QIcon(), 'Guardar como...', self)
		self.saveFileAsItem.triggered.connect(self.saveFileAs)

		self.saveFileItem = QAction(QIcon(), 'Guardar', self)
		self.saveFileItem.setEnabled(False)
		self.saveFileItem.triggered.connect(self.saveFile)

		self.exportFileItem = QAction(QIcon(), 'Exportar', self)
		self.exportFileItem.setEnabled(False)
		self.exportFileItem.triggered.connect(self.exportFile)

		self.exportFileAsItem = QAction(QIcon(), 'Exportar como...', self)
		self.exportFileAsItem.triggered.connect(self.exportFileAs)

		self.loadPresetItem = QAction(QIcon(), 'Cargar preset', self)
		self.loadPresetItem.triggered.connect(self.loadPreset)

		self.savePresetItem = QAction(QIcon(), 'Guardar preset', self)

		self.savePresetItem.triggered.connect(self.savePreset)

		self.closeAppItem = QAction(QIcon(), 'Salir', self)
		self.closeAppItem.triggered.connect(self.close)

		self.massWritingItem = QAction(QIcon(), 'Escritura masiva', self)
		self.massWritingItem.triggered.connect(self.promptBatch)

		self.autolinkItem = QAction(QIcon(), 'Generar enlaces', self)
		self.autolinkItem.triggered.connect(self.promptAutolink)

		self.chatGPTItem = QAction(QIcon(), 'Chat AT', self)
		self.chatGPTItem.triggered.connect(self.showChat)

		self.apiKeyItem = QAction(QIcon(), 'Clave de la API', self)
		self.apiKeyItem.triggered.connect(self.setAPIkey)

		self.confItem = QAction(QIcon(), 'Configuración', self)
		self.confItem.triggered.connect(self.showConfDialog)

		self.aboutAtwood = QAction(QIcon(), 'Acerca de...', self)
		self.aboutAtwood.triggered.connect(self.about)

		self.fileMenu = self.menuBar.addMenu('Archivo')
		self.fileMenu.addAction(self.newFileItem)
		self.fileMenu.addAction(self.openFileItem)
		self.fileMenu.addAction(self.saveFileItem)
		self.fileMenu.addAction(self.saveFileAsItem)
		self.fileMenu.addAction(self.exportFileItem)
		self.fileMenu.addAction(self.exportFileAsItem)
		self.fileMenu.addAction(self.loadPresetItem)
		self.fileMenu.addAction(self.savePresetItem)
		self.fileMenu.addAction(self.closeAppItem)

		self.toolsMenu = self.menuBar.addMenu('Herramientas')
		self.toolsMenu.addAction(self.massWritingItem)
		self.toolsMenu.addAction(self.autolinkItem)
		self.toolsMenu.addAction(self.chatGPTItem)

		self.confMenu = self.menuBar.addMenu('Configuración')
		self.confMenu.addAction(self.apiKeyItem)
		self.confMenu.addAction(self.confItem)

		self.helpMemu = self.menuBar.addMenu('Ayuda')
		self.helpMemu.addAction(self.aboutAtwood)

	def createTopicWidgets(self):
		self.topicLabel = QLabel()
		self.topicLabel.setText('Título')
		self.topicLineEdit = QLineEdit()
		self.topicLineEdit.textChanged.connect(self.updateGUI)
		self.mainLayout.addWidget(self.topicLabel, 1, 0, 1, 3)
		self.mainLayout.addWidget(self.topicLineEdit, 2, 0, 1, 3)

	def createAuthorWidgets(self):
		self.authorLabel = QLabel()
		self.authorLabel.setText('Autor')
		self.authorLineEdit = QLineEdit()
		self.authorLineEdit.textChanged.connect(self.updateGUI)
		self.mainLayout.addWidget(self.authorLabel, 3, 0, 1, 3)
		self.mainLayout.addWidget(self.authorLineEdit, 4, 0, 1, 3)

	def createStyleWidgets(self):
		self.styleLabel = QLabel()
		self.styleLabel.setText('Tono y estilo')
		self.styleTextEdit = QTextEdit()
		self.styleTextEdit.textChanged.connect(self.updateGUI)
		self.styleTextEdit.setMaximumSize(QSize(10000, 55))
		self.mainLayout.addWidget(self.styleLabel, 5, 0, 1, 3)
		self.mainLayout.addWidget(self.styleTextEdit, 6, 0, 1, 3)

	def createReaderWidgets(self):
		self.readerLabel = QLabel()
		self.readerLabel.setText('Lector')
		self.readerTextEdit = QTextEdit()
		self.readerTextEdit.textChanged.connect(self.updateGUI)
		self.readerTextEdit.setMaximumSize(QSize(10000, 55))
		self.mainLayout.addWidget(self.readerLabel, 7, 0, 1, 3)
		self.mainLayout.addWidget(self.readerTextEdit, 8, 0, 1, 3)

	def createInstructionsWidgets(self):
		self.instructionsLabel = QLabel()
		self.instructionsLabel.setText('Instrucciones adicionales')
		self.instructionsTextEdit = QTextEdit()
		self.instructionsTextEdit.textChanged.connect(self.updateGUI)
		self.instructionsTextEdit.setMaximumSize(QSize(10000, 75))
		self.mainLayout.addWidget(self.instructionsLabel, 9, 0, 1, 3)
		self.mainLayout.addWidget(self.instructionsTextEdit, 10, 0, 1, 3)

	def createIndexWidgets(self):
		self.indexLayout = QGridLayout()
		self.mainLayout.addLayout(self.indexLayout, 11, 0, 3, 3)
		self.indexLabel = QLabel()
		self.indexLabel.setText('Índice de contenidos')
		self.smallEntryCheckbox = QCheckBox()
		self.smallEntryCheckbox.setChecked(False)
		self.smallEntryCheckbox.setText('Texto simple')
		self.smallEntryCheckbox.clicked.connect(self.smallEntryMessage)
		self.indexTextEdit = QTextEdit()
		self.indexTextEdit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap);
		self.indexTextEdit.setStyleSheet('QTextEdit:disabled {color:white}')
		self.indexTextEdit.textChanged.connect(self.updateGUI)
		#self.indexTextEdit.setMaximumSize(QSize(10000, 1000))
		self.indexLayout.addWidget(self.indexLabel, 0, 0, 1, 1)
		self.indexLayout.addWidget(self.smallEntryCheckbox, 2, 0, 1, 1)
		self.indexLayout.addWidget(self.indexTextEdit, 1, 0, 1, 3)
		#self.mainLayout.setRowStretch(11, 2)

	def createSuggestIndexButton(self):
		self.suggestIndexButton = QPushButton()
		self.suggestIndexButton.setIcon(QIcon(os.path.join(media_directory, 'suggest-index.png')))
		self.suggestIndexButton.setStyleSheet('QPushButton:disabled {color:white}')
		self.suggestIndexButton.clicked.connect(self.promptForIndex)
		self.suggestIndexButton.setMaximumSize(32, 32)
		self.suggestIndexButton.setStyleSheet("QPushButton { padding: 7px; }")

		movie = QMovie(os.path.join(media_directory, 'loading.gif'))
		movie.setScaledSize(QSize(14, 14))
		self.gifLabel = QLabel()
		self.gifLabel.setMaximumSize(14, 14)
		self.gifLabel.setMovie(movie)
		self.gifLabel.setVisible(False)
		movie.start()

		button_layout = QVBoxLayout(self.suggestIndexButton)
		button_layout.addWidget(self.gifLabel)

		self.indexLayout.addWidget(self.suggestIndexButton, 2, 2, 1, 1)

	def createWriteButton(self):
		self.writeButton = QPushButton()
		self.writeButton.setText('¡Escribir!')
		self.writeButton.clicked.connect(self.prompt)
		self.mainLayout.addWidget(self.writeButton, 14, 0, 1, 1)

	def createCancelButton(self):
		self.cancelButton = QPushButton()
		self.cancelButton.setText('Cancelar')
		self.cancelButton.setEnabled(False)
		self.cancelButton.clicked.connect(lambda: self.finalizeTasks(stopped=True))
		self.mainLayout.addWidget(self.cancelButton, 14, 1, 1, 1)

	def createEditorTextEdit(self):
		self.editorTextEdit = QTextEdit()
		self.editorTextEdit.setStyleSheet('''QTextEdit:disabled {color:white;}''')
		self.editorTextEdit.focusOutEvent = self.placeCursor
		self.editorTextEdit.textChanged.connect(self.updateGUI)
		self.mainLayout.addWidget(self.editorTextEdit, 2, 3, 12, 9)

	def createStatusBar(self):
		self.statusBar = QStatusBar()
		self.mainLayout.addWidget(self.statusBar, 14, 2, 1, 4)

	def createMetaCheckbox(self):
		self.metaCheckBox = QCheckBox()
		self.metaCheckBox.setText('Metadescripción')
		self.metaCheckBox.setChecked(True)
		self.mainLayout.addWidget(self.metaCheckBox, 14, 9, 1, 1)

	def createAutointroCheckbox(self):
		self.autointroCheckBox = QCheckBox()
		self.autointroCheckBox.setText('Intro. automática')
		self.autointroCheckBox.setChecked(True)
		self.mainLayout.addWidget(self.autointroCheckBox, 14, 10, 1, 1)

	def createAutolinkCheckbox(self):
		self.autolinkCheckBox = QCheckBox()
		self.autolinkCheckBox.setText('Autoenlazar')
		self.autolinkCheckBox.setChecked(False)
		self.autolinkCheckBox.clicked.connect(self.autolinkWarning)
		self.mainLayout.addWidget(self.autolinkCheckBox, 14, 11, 1, 1)

	def createShowTitleCheckbox(self):
		self.showTitleCheckBox = QCheckBox()
		self.showTitleCheckBox.setText('Mostrar titulo')
		self.showTitleCheckBox.setChecked(True)
		self.mainLayout.addWidget(self.showTitleCheckBox, 14, 8, 1, 1)

	#################################################################################################
	### MESSAGE DIALOGS ###
	#################################################################################################

	def infoMessage(self, message, title = ''):
		self.infoMessageDialog = QMessageBox()
		self.infoMessageDialog.setIcon(QMessageBox.Information)
		self.infoMessageDialog.setText(message)
		self.infoMessageDialog.setWindowTitle("Información" if not len(title) else title)
		self.infoMessageDialog.setStandardButtons(QMessageBox.Ok)
		self.infoMessageDialog.exec_()	

	def warningMessage(self, message):
		self.warningMessageDialog = QMessageBox()
		self.warningMessageDialog.setIcon(QMessageBox.Warning)
		self.warningMessageDialog.setText(message)
		self.warningMessageDialog.setWindowTitle("Advertencia")
		self.warningMessageDialog.setStandardButtons(QMessageBox.Ok)
		self.warningMessageDialog.exec_()	

	def askMessage(self, title, message, yes='Sí', no='No'):
		self.askMessageDialog = QMessageBox()
		self.askMessageDialog.setIcon(QMessageBox.Question)
		self.askMessageDialog.setText(message)
		self.askMessageDialog.setWindowTitle(title)
		self.askMessageDialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		self.askMessageDialog.button(QMessageBox.Yes).setText(yes)
		self.askMessageDialog.button(QMessageBox.No).setText(no)

		return self.askMessageDialog.exec_()	

	def errorMessage(self, message, title = 'Error', exc_info=False):
		print(f'ERROR: {message}')
		self.errorMessageDialog = QMessageBox()
		self.errorMessageDialog.setIcon(QMessageBox.Critical)
		self.errorMessageDialog.setText(message)
		self.errorMessageDialog.setWindowTitle(title)
		self.errorMessageDialog.setStandardButtons(QMessageBox.Ok)
		self.errorMessageDialog.exec_()

		if exc_info:
			excinfo = sys.exc_info()
			print('INFORMACION DE LA EXCEPCION: %s' % exc_info)

	#################################################################################################
	### GUI METHODS ##
	#################################################################################################

	def about(self):
		message = '''
		Esta es una aplicación en desarrollo. Prohibida su distribución. Nelson Ochagavía © 2023. Email: <a href="mailto:nelson.ochagavia@gmail.com">nelson.ochagavia@gmail.com</a>'''.strip()
		self.infoMessage(title = 'Acerca de Atwood %s' % version, message = message)

	def showChat(self):
		if not self.chatbot.isVisible():
			self.chatbot.show()

	def showConfDialog(self):
		self.confDialog.exec_()
		self.loadWritingConfig()

	def setAPIkey(self):
		apikey, ok = QInputDialog.getText(self, 'Clave de la API', 'Escribe o pega tu clave de la API de OpenAI.')

		if ok:

			if not len(apikey.strip()):
				self.infoMessage('¡Introduce la clave!')
				return self.setAPIkey()

			secret.write_file(self.mistery, apikey_file, apikey.strip())
			self.apikey = self.getAPIKey()
			openai.api_key = self.apikey

			if self.testAPIKey():
				self.infoMessage('¡La clave fue instalada correctamente!')
			else:
				self.errorMessage('Lo siento, la clave es incorrecta.')

	def getAPIKey(self, first=False):
		try:
			return secret.read_file(self.mistery, apikey_file)
		except:
			if first:
				self.infoMessage('Por favor, inserta la clave de la API de OpenAI para empezar a usar Atwood.')
			else:
				self.errorMessage('Problema al leer la clave de la API. Contacta con el desarrollador.')
			return ''

	def testAPIKey(self):
		try:
			openai.Completion.create(
					engine = 'ada',
					prompt = 'Hola ',
					temperature = 0,
					top_p = 0,
				)
		except openai.error.AuthenticationError:
			return False

		return True
	
	def smallEntryMessage(self):
		if self.autointroCheckBox.isChecked():
			self.autointroCheckBox.setChecked(False)
			self.warningMessage('Activaste el modo texto simple. Se desactivó la introducción automática y se ignorará el índice.')
		else: 
			if len(self.indexTextEdit.toPlainText().strip()):
				self.warningMessage('Activaste el modo texto simple. Se ignorará el índice.')

	def autolinkWarning(self):
		if self.autolinkCheckBox.isChecked():
			response = self.askMessage(title='Confirmar enlazado automático', message='El enlazado automático es un proceso lento. ¿Confirmas que deseas continuar?')
			if response == QMessageBox.Yes:
				self.infoMessage('¡Bien! El enlazado automático se añadirá a las actividades de escritura.')
			else:
				self.autolinkCheckBox.setChecked(False)

	def updateGUI(self, modified = True):

		if modified:
			self.fileSaved = False
		else:
			self.fileSaved = True

		if len(self.filename):
			self.docName = mu.basenameNoExt(self.filename)
		else:
			self.docName = self.topicLineEdit.text().strip()
			self.docName = mu.removeLastDot(self.docName).strip()
			self.docName = mu.basenameNoExt(self.docName)
		
		fileSavedIndicator = '*' if not self.fileSaved else ''
		windowTitle = '%s %s | Atwood %s' % (fileSavedIndicator, self.docName, version)

		self.setWindowTitle(windowTitle)

		if not self.interactionBlocked:
			self.autolinkItem.setEnabled(True if len(self.editorTextEdit.toPlainText().strip()) else False)

	def readPresetFile(self, filename):

		data = {}
		try:
			with open(filename, 'r') as file:
				try:
					data = json.load(file)
				except Exception as e:
					self.errorMessage('El archivo de preset tiene un formato incorrecto.')
					return
		except Exception as e:
				self.errorMessage('El archivo de preset no existe.', exc_info = True)
				return

		self.authorLineEdit.setText(data['author'])
		self.styleTextEdit.setText(data['style'])
		self.readerTextEdit.setText(data['reader'])
		self.instructionsTextEdit.setText(data['extra'])  
		self.metaCheckBox.setChecked(data['meta'])
		self.autointroCheckBox.setChecked(data['auto-intro']) 

		self.updateGUI()

	def writePresetFile(self, filename):

		data = self.recollect()

		try:
			del data['scope']
			del data['index']
		except Exception as e:
			printwarn('Advertencia', '%s' % e)

		#print('Preset File: ' + filename)

		try:
			with open(filename, 'w') as file:
				#print('Salvar preset')
				json.dump(data, file, indent=4)
		except Exception as e:
			self.errorMessage('No se pudo guardar el archivo de preset.', exc_info = True)
			return

		self.updateGUI()


	def readAtwFile(self, filename):

		'''with io.open(filename + '.writer.json', mode='r', encoding='utf-8') as file:
			currWriterData = file.read()
			parsed_dict = json.loads(currWriterData)
			print(parsed_dict)
			#self.currWriter = AtWriter(parsed_dict['value'])'''

		data = {}

		try:
			with open(filename, 'r') as file:
				try:
					data = json.load(file)
				except Exception as e:
					self.errorMessage('El documento tiene un formato incorrecto.', exc_info = True)

				self.topicLineEdit.setText(data.get('scope', ''))
				self.authorLineEdit.setText(data.get('author', ''))
				self.styleTextEdit.setText(data.get('style', ''))
				self.readerTextEdit.setText(data.get('reader', ''))
				self.instructionsTextEdit.setText(data.get('extra', ''))

				index = data['index']
				indexStr = ''

				for entry in index:
					if len(entry.strip()):
						if entry[0] == '\t':
							indexStr = indexStr + '\t%s\n' % entry.strip()
						else:
							indexStr = indexStr + '%s\n' % entry.strip()

				self.indexTextEdit.setPlainText(indexStr)
				self.smallEntryCheckbox.setChecked(data.get('small-entry', False))
				self.metaCheckBox.setChecked(data.get('meta', True))
				self.autointroCheckBox.setChecked(data.get('auto-intro', True))
				self.autolinkCheckBox.setChecked(data.get('autolink', False))
				self.showTitleCheckBox.setChecked(data.get('show-title', True))
				self.editorTextEdit.clear()
				self.editorTextEdit.insertHtml(data.get('content', ''))
				self.keywords = data.get('keywords')

				try:
					self.indexProgress = data['index-progress']
				except Exception as e:
					self.errorMessage('No se pudo recuperar el estado de progreso del documento.', exc_info = True)

		except Exception as e:
			self.errorMessage('El archivo no existe.')  
			print('ERROR in readAtwFile(): %s' % e)  

	def writeAtwFile(self, filename):

		data = self.recollect()
		data['content'] = self.editorTextEdit.toHtml()
		data['index-progress'] = self.indexProgress
		data['keywords'] = self.keywords

		'''currWriterData = json.dumps(self.currWriter.__dict__)

		with io.open(filename + '.writer.json', mode='w', encoding='utf-8') as file:
			file.write(currWriterData)'''

		try:
			#print(filename)
			with open(filename, 'w') as file:
				json.dump(data, file, indent=4)
		except Exception as e:
			self.errorMessage('No se pudo guardar el documento.', exc_info = True)

		self.updateGUI()


	def exportHtmlFile(self, filename):
		html = self.editorTextEdit.toMarkdown()
		markdown = mu.fix_markdown_line_breaks(html)
		#print('\nEXPORTAR:\n\n%s' % markdown)
		lines = markdown.split('\n\n')
		clean = ''

		for line in lines:
			sline = line.strip()
			#print(f'MARKDOWN STRIPED LINE: {sline}')
			clean = clean + mu.convertHeading(sline) + "\n\n"

		clean = clean.strip() 

		#print('\nCONTENIDO CON CORRECTO FORMATO:\n\n%s' % clean)

		html = md.markdown(clean)

		#print('\nHTML A GUARDAR:\n\n%s' % html)

		try:
			with open(filename, 'w') as file:
				file.write(html)
		except Exception as e:
			self.errorMessage('No se pudo exportar el documento.', exc_info = True)

	def backupAtwFile(self):

		filename = '%s.atb' % self.docName
		platform = mu.get_platform().lower()

		if platform == 'linux':
			path = os.path.join(default_doc_directory, '.' + filename)
		else:
			path = os.path.join(default_doc_directory, '~' + filename)

		try:
			self.writeAtwFile(path)
		except Exception as e:
			print('ERROR AL RESPALDAR DOCUMENTO. EXCEPCION: %s' % str(e))

	def isThereContent(self):
		data = self.recollect()
		try:
			del data['auto-intro']
			del data['meta']
			#del data['autolink']
		except Exception as e:
			printwarn('Advertencia', '%s' % e)

		data['content'] = self.editorTextEdit.toHtml()

		for key, value in data.items():
			if len(value):
				return True

		return False

	def newFile(self):

		if self.isThereContent():

			if not self.fileSaved:
				reply = QMessageBox.question(self, 'Nuevo documento', "¿Estás seguro que deseas crear un nuevo documento? Los cambios que no hayas guardado se perderán.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
			else:
				reply = QMessageBox.Yes
			
			if reply == QMessageBox.Yes:
				self.topicLineEdit.clear()
				self.authorLineEdit.clear()
				self.styleTextEdit.clear()
				self.readerTextEdit.clear()
				self.instructionsTextEdit.clear()
				self.indexTextEdit.clear()
				self.editorTextEdit.clear()

				self.cdots = 1
				self.cancelled = False
				self.fileSaved = False
				self.fileSaved = False
				self.indexProgress = []
				self.docName = 'Documento sin título'
				self.filename = os.path.join(os.getcwd(), self.docsFolder, self.docName)
				self.expFileName = os.path.join(os.getcwd(), self.docsFolder, self.docName)
				self.expExt = 'docx'
				self.writer = None
				self.writingThread = None
				self.indexWriter = None
				self.indexThread = None
				self.suggestedIndex = ''
				self.keywords = []
				self.batchDataIndex = []
				self.err = False
				self.cancelled = False
				self.printQueue = []
				self.indexProgress = []	
				self.interactionBlocked = False

				self.saveFileItem.setEnabled(False)
				self.exportFileItem.setEnabled(False)

				self.updateGUI()

	def openFile(self):
		mu.mkDirIfNotExists(self.docsFolder)
		filename, filetype = QFileDialog.getOpenFileName(self, 'Abrir documento', self.docsFolder, doc_ext[1])
		
		if len(filename):
			self.filename = filename
			self.readAtwFile(filename)
			self.fileSaved = True
			self.saveFileItem.setEnabled(True)
			self.exportFileItem.setEnabled(False)
			self.updateGUI(modified = False)

	def saveFile(self):
		if not self.fileSaved:
			filename = mu.filenameNoExt(self.filename) + '.%s' % doc_ext[0]
			self.writeAtwFile(filename)
			self.fileSaved = True
			self.updateGUI(modified=False)

	def saveFileAs(self):
		mu.mkDirIfNotExists(self.docsFolder)

		if self.docName == default_doc_name:
			topic = self.topicLineEdit.text().strip()

			if len(topic):
				defaultFileName = mu.toValidFileName(topic)
			else:
				defaultFileName = mu.toValidFileName(self.topicLineEdit.placeholderText())
		else:

			defaultFileName = mu.filenameNoExt( mu.toValidFileName(self.docName) )

		filename, filetype = QFileDialog.getSaveFileName(self, 'Guardar documento', os.path.join(self.docsFolder, defaultFileName), doc_ext[1])


		if len(filename):
			self.filename = mu.filenameNoExt(filename) + '.%s' % doc_ext[0]
			self.writeAtwFile(self.filename)
			self.fileSaved = True
			self.saveFileItem.setEnabled(True)
			self.updateGUI(modified=False)

	def exportFile(self):	
		self.expFileName = mu.filenameNoExt(self.expFileName) + '.%s' % self.expExt
		self.exportHtmlFile(self.expFileName)

	def exportFileAs(self):
		mu.mkDirIfNotExists(self.docsFolder)

		if self.docName == default_doc_name:
			topic = self.topicLineEdit.text().strip()

			if len(topic):
				defaultFileName = mu.toValidFileName(topic)
			else:
				defaultFileName = mu.toValidFileName(self.topicLineEdit.placeholderText())
		else:

			defaultFileName = mu.filenameNoExt( mu.toValidFileName(self.docName) )

		filename, filetype = QFileDialog.getSaveFileName(self, 'Exportar como...', os.path.join(self.docsFolder, defaultFileName), '%s;;%s;;%s' % (export_exts[0][1], export_exts[1][1], export_exts[2][1]))

		if len(filename):
			ext = ''
			for ex in export_exts:
				if ex[1] == filetype:
					ext = ex[0]
			
			self.expFileName = mu.filenameNoExt(filename) + '.%s' % ext
			self.expExt = ext
			self.exportFileItem.setEnabled(True)
			self.exportHtmlFile(self.expFileName)

	def loadPreset(self):
		mu.mkDirIfNotExists(self.presetsFolder)
		filename, filetype = QFileDialog.getOpenFileName(self, 'Cargar preset', self.presetsFolder, pst_ext[1])
		if len(filename):
			self.readPresetFile(filename)

	def savePreset(self):
		mu.mkDirIfNotExists(self.presetsFolder)
		defaultFileName = mu.toValidFileName(self.authorLineEdit.text())
		filename, filetype = QFileDialog.getSaveFileName(self, 'Guardar preset', os.path.join(self.presetsFolder, defaultFileName), pst_ext[1])
		filename = mu.filenameNoExt(filename) + '.%s' % pst_ext[0]
		#print('FILENAME: ' + filename)
		if len(filename):
			self.writePresetFile(filename)


	def setUserInteraction(self, value):
		self.interactionBlocked = not value
		self.indexTextEdit.setReadOnly(not value)
		self.smallEntryCheckbox.setEnabled(value)
		self.editorTextEdit.setEnabled(value)
		self.writeButton.setEnabled(value)
		self.cancelButton.setEnabled(not value)
		self.writeButton.setEnabled(value)
		self.suggestIndexButton.setEnabled(value)
		self.metaCheckBox.setEnabled(value)
		self.autointroCheckBox.setEnabled(value)
		self.autolinkCheckBox.setEnabled(value)
		self.showTitleCheckBox.setEnabled(value)
		self.newFileItem.setEnabled(value)
		self.openFileItem.setEnabled(value)
		self.saveFileItem.setEnabled(value)
		self.saveFileAsItem.setEnabled(value)
		self.exportFileItem.setEnabled(value)
		self.exportFileAsItem.setEnabled(value)
		self.loadPresetItem.setEnabled(value)
		self.savePresetItem.setEnabled(value)
		self.apiKeyItem.setEnabled(value)
		self.confItem.setEnabled(value)
		self.massWritingItem.setEnabled(value)
		self.autolinkItem.setEnabled(value)


	#################################################################################################
	### WRITING METHODS ###
	#################################################################################################

	def prepareToWrite(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} prepareToWrite()")
		
		self.cancelled = False
		self.currArticle = ''
		self.dots = -1
		self.cancelled = False
		self.indexProgress = []
		self.textQueue = []
		self.printQueue = []
		self.fileSaved = False
		self.writer = None
		self.writingThread = None
		self.indexWriter = None
		self.indexThread = None
		self.unfinishedArtWriter = None
		self.unfinishedArtData = None
		self.err = False
		self.placeCursor()
		self.setUserInteraction(False)

	def finalizeTasks(self, stopped = False, err = False):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} finalizeTasks()")

		if stopped:
			self.cancelled = True

		if err:
			self.err = True

		self.cancelButton.setEnabled(False)

		if not self.finalizeTasksThread.isRunning():
			self.finalizeTasksThread.start()
	
	def postActivityTasks(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} postActivityTasks()")
		self.setUserInteraction(True)

		if self.cancelled:
			self.cancelled = False
			self.errorMessage('Actividad cancelada.', 'Cancelación')
			return
		
		if self.err:
			self.err = False
			self.errorMessage('La actividad finalizó con errores.')
			return
		
		
		self.infoMessage('La actividad finalizó con éxito.')

		#print('\nMARKDOWN:\n\n%s' % self.editorTextEdit.toMarkdown())

		#print('\nHTML:\n\n%s' % self.editorTextEdit.toHtml())

	def placeCursor(self, e=None):
		self.editorTextEdit.moveCursor(QTextCursor.EndOfLine)		
	
	def removeMessage(self):
		cursor = self.editorTextEdit.textCursor()
		cursor.movePosition(QTextCursor.StartOfLine)
		p = cursor.position()
		cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
		sel = cursor.selectedText()
		cursor.removeSelectedText()
		cursor.movePosition(p)
		

	def localizeCurrentIndexEntry(self, string):
		#print(f"{Fore.GREEN}FUNC:{Fore.WHITE} localizeCurrentIndexEntry()")
		text = self.indexTextEdit.toPlainText()
		pos = text.find(string)
	
		if pos != -1:
			cursor = self.indexTextEdit.textCursor()
			cursor.setPosition(pos, QTextCursor.MoveAnchor)
			self.indexTextEdit.setTextCursor(cursor)
			return cursor
	
		return None

	
	def change_font_color(self, message, color):
		#print(f"{Fore.GREEN}FUNC:{Fore.WHITE} change_font_color()")
		if message.find('Escribiendo') > -1:

			toks = self.remove_html_tags(message).split('"')

			if len(toks) > 1:
				entry = toks[1]
			else:
				return
			cursor = self.localizeCurrentIndexEntry(entry)

			if cursor:
				cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)

				# Get cursor and current char format
				#cursor = self.indexTextEdit.textCursor()
				f = cursor.charFormat()

				# Set foreground color to selected text only
				if not cursor.hasSelection():
					return
				else:
					f.setForeground(QColor(color))
					cursor.setCharFormat(f)	
					self.indexTextEdit.ensureCursorVisible()

	def remove_html_tags(self, text):
		clean = re.compile('<.*?>')
		return re.sub(clean, '', text)

	def insertMessage(self, message):

		if self.cancelled:

			if self.cdots > 4:
				self.cdots = 1

			message = '<p style="color:#ff5349"><i>Cancelando.%s</i></p>' % ('.' * self.cdots)
			self.cdots += 1

			self.editorTextEdit.insertHtml(message)

		else:
			#self.change_font_color(message, 'yellow')
			#self.markCurrentIndexEntry(message) #puesto como comentario hasta que implemente bien esa funcion
			self.editorTextEdit.insertHtml(message)
			self.editorTextEdit.ensureCursorVisible()

	def messageLoop(self, message):
		#print(f"{Fore.GREEN}FUNC:{Fore.WHITE} messageLoop()")

		if self.messageThread:
			self.messageThread.cancellate()
			self.removeMessage()

		self.messageThread = MessageLoopThread(self, message)
		self.messageThread.clean.connect(self.removeMessage)
		self.messageThread.update[str].connect(self.insertMessage)
		self.messageThread.finished.connect(lambda: self.removeMessage)
		self.messageThread.start()

	def updateText(self, content):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} updateText()")

		if self.messageThread:
			self.messageThread.cancellate()
			self.messageThread.wait()
			self.removeMessage()

		self.editorTextEdit.insertHtml(content)
		self.editorTextEdit.ensureCursorVisible()
		self.currArticleEnd = self.editorTextEdit.textCursor().position()

		self.writeAtwFile(self.filename)

		#print('CONTENIDO INSERTADO:\n%s\n' % content)
		#print('CONTENIDO DEL EDITOR:\n%s\n' % self.editorTextEdit.toMarkdown())

	def error(self, error, writer = None, data = None):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} error()")
		if writer and data:
			#print('DATA IN ERROR(): %s' % data)
			self.unfinishedArtWriter = writer
			self.unfinishedArtData = data
			
			response = RetryDialog().exec_()
			if response == QDialog.Accepted:
				if self.writingMode == 'article':
					self.continueArticle()
				elif self.writingMode == 'batch':
					self.writeBatchArtice(recuperate = self.unfinishedArtWriter)
			else:
				self.finalizeTasks(err=True)
		else:
			self.errorMessage(error)
			self.finalizeTasks(err=True)

	def insertLink(self, term, a):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} insertLink()")
		if self.messageThread:
			self.messageThread.cancellate()
			self.messageThread.wait()
			self.removeMessage()

		#print('IN INSERTLINK(), TERM: %s A: %s' %(term, a))
		text = self.editorTextEdit.toHtml()
		lines = text.splitlines()
		linkedText = ''
		inserted = False
		for line in lines:
			if line.find('<h1') == -1 and line.find('name="meta"') == -1 and line.find('<h2') == -1:
				if line.find(term) > -1 and not inserted:
					newline = line.replace(term, a, 1)
					inserted = True
				else:
					newline = line
			else:
				newline = line
			linkedText = linkedText + newline + '\n'
				
		self.editorTextEdit.setHtml(linkedText)
		self.editorTextEdit.moveCursor(QTextCursor.End)


	def getWritingConfig(self):
		#print(f"{Fore.GREEN}FUNC:{Fore.WHITE} getWritingConfig()")
		conf = {}
		conf['writer'] = {}
		conf['alconf'] = {}
		conf['writer']['engine'] = self.conf['engine']
		conf['writer']['retries_after_error'] = self.conf['retries_after_error']
		conf['writer']['error_latency'] = self.conf['error_latency']
		conf['writer']['error_latency'] = self.conf['error_latency']
		conf['writer']['temperature'] = self.conf['temperature']
		conf['writer']['top_p'] = self.conf['top_p']
		conf['writer']['frequency_penalty'] = self.conf['frequency_penalty']
		conf['writer']['presence_penalty'] = self.conf['presence_penalty']
		conf['writer']['max_tokens'] = self.conf['max_tokens']
		conf['writer']['retries'] = self.conf['retries']
		conf['writer']['latency'] = self.conf['latency']
		conf['alconf']['min_kw'] = self.conf['min_kw']
		conf['alconf']['max_kw'] = self.conf['max_kw']
		conf['alconf']['tld'] = self.conf['tld']
		conf['alconf']['num'] = self.conf['num']
		conf['alconf']['stop'] = self.conf['stop']
		conf['alconf']['pause'] = self.conf['pause']
		conf['alconf']['delay'] = self.conf['delay']

		#print('CONFIGURATION:\n%s' % json.dumps(conf, indent=4))

		return conf

	def recollect(self):
		#print(f"{Fore.GREEN}FUNC:{Fore.WHITE} recollect()")	

		data = {}

		if not len(self.topicLineEdit.text().strip()):
			data['scope'] = self.topicLineEdit.placeholderText().strip()
		else:
			data['scope'] = self.topicLineEdit.text().strip()

		if not len(self.authorLineEdit.text().strip()):
			data['author'] = self.authorLineEdit.placeholderText().strip()
		else:
			data['author'] = self.authorLineEdit.text().strip()

		if not len(self.styleTextEdit.toPlainText().strip()):
			data['style'] = self.styleTextEdit.placeholderText().strip()
		else:
			data['style'] = self.styleTextEdit.toPlainText().strip()

		if not len(self.readerTextEdit.toPlainText().strip()):
			data['reader'] = self.readerTextEdit.placeholderText().strip()
		else:
			data['reader'] = self.readerTextEdit.toPlainText().strip()

		if not len(self.instructionsTextEdit.toPlainText().strip()):
			data['extra'] = self.instructionsTextEdit.placeholderText().strip()
		else:
			data['extra'] = self.instructionsTextEdit.toPlainText().strip()

		data['index'] = []
		data['small-entry'] = self.smallEntryCheckbox.isChecked()

		if not data['small-entry']:
			indexLines = ''

			if not len(self.indexTextEdit.toPlainText().strip()):
				if not self.smallEntryCheckbox.isChecked():
					indexLines = self.indexTextEdit.placeholderText().strip().split('\n')
			else:
				indexLines = self.indexTextEdit.toPlainText().strip().split('\n')		

			if len(indexLines):
				for line in indexLines:
					if str(line.strip()):
						if line[0] == '\t':
							data['index'].append('\t' + line.strip())
						else:
							data['index'].append(line.strip())

		data['meta'] = self.metaCheckBox.isChecked()
		data['auto-intro'] = self.autointroCheckBox.isChecked()
		data['autolink'] = self.autolinkCheckBox.isChecked()
		data['show-title'] = self.showTitleCheckBox.isChecked()

		conf = self.getWritingConfig()
		data['writer'] = conf['writer']
		data['alconf'] = conf['alconf']

		return data

	def prompt(self, wait = 0, recuperate=None, rec_data=None):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} prompt()")	
		self.writingMode = 'article'
		self.prepareToWrite()

		if not rec_data:
			data = self.recollect()
			data['wait'] = wait
		else:
			data = rec_data

		if len(data['index']) == 1 and not data['auto-intro']:
			self.autointroCheckBox.setChecked(True)
			data['auto-intro'] = True
			self.warningMessage('El índice tiene una sola entrada. Se activó la introducción automática.')

		if len(data['index']) == 0:
			if self.autointroCheckBox.isChecked():
				self.autointroCheckBox.setChecked(False)
				data['auto-intro'] = False
				self.warningMessage('Se desactivó la introducción automática para escribir un texto simple')

		data['fast_testing_mode'] = fast_testing_mode
		self.setUserInteraction(False)

		#print('RECUPERATE VALUE INSIDE PROMPT(): %s' % recuperate)

		if not recuperate:
			self.writingThread = ArticleThread(self, self.apikey, data)
		else:
			self.writingThread = ArticleThread(self, self.apikey, data, recuperate)

		self.writingThread.message[str].connect(self.messageLoop)
		self.writingThread.writerSignal[AtWriter].connect(self.setCurrWriter)
		self.writingThread.text[str].connect(self.updateText)
		self.writingThread.link[str, str].connect(self.insertLink)
		self.writingThread.error[str, AtWriter, dict].connect(self.error)
		self.writingThread.stopped[AtWriter, dict].connect(self.writingStop)
		self.writingThread.finished.connect(self.writingFinalize)
		self.writingThread.start()

	def setCurrWriter(self, writer):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} setCurrWriter()")
		self.currWriter = writer

	def continueArticle(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} continueArticle()")
		self.prompt(recuperate = self.unfinishedArtWriter, rec_data = self.unfinishedArtData)

	def writingFinalize(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} writingFinalize()")	
		self.finalizeTasks()

	def writingStop(self, writer, data):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} writingStop()")
		#print('WRITER: %s' % writer)
		self.unfinishedArtWriter = writer
		self.unfinishedArtData = data
		self.finalizeTasks(True)
	
	def writeBatchArtice(self, recuperate=None):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} writeBatchArticle()")

		if self.bindex >= len(self.keywords):
			print(f"{Fore.GREEN}FINALIZADO CON: {Fore.WHITE}{self.bindex} de {len(self.keywords)}")
			self.finalizeTasks()
			return

		if self.cancelled:
			print(f"{Fore.YELLOW}LA BANDERA CANCELLED SE ACTIVO. LOTE FINALIZADO.")
			return

		print(f"{Fore.GREEN}ESCRIBIENDO ARTICULO: {Fore.WHITE}{self.bindex} de {len(self.keywords)}")
		self.prepareToWrite()		
		self.bdata[self.bindex]['wait'] = 0 if self.bindex == 0 else 5

		if not recuperate:
			self.writingThread = ArticleThread(self, self.apikey, self.bdata[self.bindex])
		else:
			self.writingThread = ArticleThread(self, self.apikey, self.bdata[self.bindex], recuperate)

		self.writingThread.writerSignal[AtWriter].connect(self.setCurrWriter)
		self.writingThread.message[str].connect(self.messageLoop)
		self.writingThread.text[str].connect(self.updateText)
		self.writingThread.error[str, AtWriter, dict].connect(self.error)
		self.writingThread.finished.connect(self.nextBatchArticle)
		self.writingThread.start()	

	def continueBatch(self):
		pass

	def nextBatchArticle(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} nextBatchArticle()")
		self.removeMessage()
		self.bindex += 1
		self.writeBatchArtice()

	def promptBatch(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} promptBatch()")
		dialog = KeywordsDialogs(self, self.keywords)

		if dialog.exec_():
			self.keywords = dialog.getKeywords()
			if not len(self.editorTextEdit.toPlainText().strip()):
				self.topicLineEdit.setText('LOTE - {}'.format(time.strftime("%m-%d %H-%M", time.localtime())))
			#self.filename = os.path.join(default_doc_directory, mu.toValidFileName(self.topicLineEdit.text().strip()))
			#self.updateGUI()
			self.indexTextEdit.clear()

			bdata = self.recollect()
			self.setUserInteraction(False)

			self.prepBatchThread = PrepBatchThread(self, self.apikey, self.keywords, bdata, fast_testing_mode)
			self.prepBatchThread.error[str].connect(self.error)
			self.prepBatchThread.msg[str].connect(self.messageLoop)
			self.prepBatchThread.title[str].connect(self.insertBatchArtname)
			self.prepBatchThread.checks[bool].connect(self.autointroCheckBox.setChecked)
			self.prepBatchThread.newIndex[list].connect(self.insertBatchArtindex)
			self.prepBatchThread.finished[list].connect(self.startBatchWriting)
			self.prepBatchThread.start()

			response = self.askMessage(title='¡No te aburras!', message='La escritura masiva puede demorar. ¿Quieres conversar con Chat AT?<br><br><b>PD: </b>Si te aburres luego, solo tienes que ir al menú Herramientas y hacer clic en Chat AT.', yes='¡Claro!', no='No')
			
			if response == QMessageBox.Yes:
				self.chatbot.show()
		else:
			self.keywords = dialog.getKeywords()
			#print(self.keywords)
	
	def insertBatchArtname(self, entry_name):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} insertBatchArtname()")
		if self.messageThread:
			self.messageThread.cancellate()
			self.removeMessage()
		self.indexTextEdit.append(entry_name)

	def insertBatchArtindex(self, index):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} insertBatchArtindex()")
		for entry in index:
			self.indexTextEdit.append('\t%s' % entry.strip())

	def startBatchWriting(self, bdata):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} startBatchWriting()")
		self.writingMode = 'batch'

		if self.messageThread:
			self.messageThread.cancellate()
			self.removeMessage()

		self.bdata = bdata
		self.bindex = 0

		self.writeBatchArtice()
	
	def setUserInteractionForIndexGen(self, value):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} setUserInteractionForIndexGen()")
		
		if value == False:
			self.gifLabel.setVisible(True)
			self.suggestIndexButton.setIcon(QIcon())
		else:
			self.gifLabel.setVisible(False)
			self.suggestIndexButton.setIcon(QIcon(os.path.join(media_directory, 'suggest-index')))

		self.interactionBlocked = not value
		self.indexTextEdit.setReadOnly(not value)
		self.smallEntryCheckbox.setEnabled(value)
		self.writeButton.setEnabled(value)
		#self.cancelButton.setEnabled(not value)
		self.suggestIndexButton.setEnabled(value)
		self.autointroCheckBox.setEnabled(value)
		self.metaCheckBox.setEnabled(value)
		self.autolinkCheckBox.setEnabled(value)
		self.showTitleCheckBox.setEnabled(value)
		self.writeButton.setEnabled(value)
		self.newFileItem.setEnabled(value)
		self.openFileItem.setEnabled(value)
		self.saveFileAsItem.setEnabled(value)
		self.exportFileItem.setEnabled(value)
		self.loadPresetItem.setEnabled(value)
		self.savePresetItem.setEnabled(value)
		self.apiKeyItem.setEnabled(value)
		self.confItem.setEnabled(value)
		self.massWritingItem.setEnabled(value)
		self.autolinkItem.setEnabled(value)

	def promptForIndex(self, idata = None):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} promptForIndex()")

		if not idata:
			indexFromBatch = False
			idata = self.recollect()
		else:
			indexFromBatch = True

		self.indexTextEdit.clear()
		self.setUserInteractionForIndexGen(False)
		self.indexThread = IndexThread(self, self.apikey, idata)
		self.indexThread.error[str].connect(self.error)
		if indexFromBatch:
			self.indexThread.finished[list].connect(self.updateBatchDataIndex)
		else:
			self.indexThread.finished[list].connect(self.insertIndex)
		self.indexThread.start()		

	def updateBatchDataIndex(self, index):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} updateBatchDataIndex()")
		self.batchDataIndex = index

	def insertIndex(self, index):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} insertIndex()")
		self.indexTextEdit.clear()
		for entry in index: 
			self.indexTextEdit.append(entry)
		self.setUserInteractionForIndexGen(True)

	def promptAutolink(self):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} promptAutolink()")

		response = self.askMessage(title='Confirmar enlazado automático', message='El enlazado automático es un proceso lento. ¿Confirmas que deseas continuar?')
		if response == QMessageBox.No:
			return

		self.setUserInteraction(False)
		data = self.getWritingConfig()
		content = self.editorTextEdit.toMarkdown()

		self.editorTextEdit.moveCursor(QTextCursor.End)
		self.editorTextEdit.append('')
		self.autolinkThread = AutolinkThread(self, self.apikey, content, data)
		self.autolinkThread.message[str].connect(self.messageLoop)
		self.autolinkThread.link[str, str].connect(self.insertLink)
		self.autolinkThread.error[str].connect(self.error)
		self.autolinkThread.stopped[str].connect(self.linkingStop)
		self.autolinkThread.finished[str].connect(self.linkingFinalize)
		self.autolinkThread.start()


	def linkingFinalize(self, linkedText):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} linkingFinalize()")
		self.editorTextEdit.clear()
		self.editorTextEdit.insertHtml(linkedText)
		self.finalizeTasks()

	def linkingStop(self, linkedText):
		print(f"{Fore.GREEN}FUNC:{Fore.WHITE} linkingStop()")
		self.editorTextEdit.clear()
		self.editorTextEdit.insertHtml(linkedText)
		self.finalizeTasks(True)


	#################################################################################################
	### EVENTS ###
	#################################################################################################

	def closeEvent(self, e):

		reply = self.askMessage(title='Salir', message="¿Estás seguro que deseas salir? Los cambios que no hayas guardado se perderán.")

		if reply == QMessageBox.Yes:
			e.accept()
		else:
			e.ignore()
