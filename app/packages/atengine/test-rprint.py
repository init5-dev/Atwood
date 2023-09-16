from atchat import AtChat
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

if __name__ == '__main__':
	app = QApplication([])
	win = QWidget()
	textbox = QTextEdit(win)
	win.resize(640, 480)
	win.show()
	chatbot = AtChat(apikey = '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')
	chatbot.answer('Hola', textbox.insertPlainText)
	app.exec_()