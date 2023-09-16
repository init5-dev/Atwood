import sys
from io import StringIO
from contextlib import redirect_stdout

class RedirPrint:

	def print(self, print_method, *args, **kwargs):
		with StringIO() as f:
			with redirect_stdout(f):
				print_method(*args, **kwargs)
			

if __name__ == '__main__':
	from PyQt5.QtCore import *
	from PyQt5.QtGui import *
	from PyQt5.QtWidgets import *

	app = QApplication([])
	win = QWidget()
	textbox = QTextEdit(win)
	rp = RedirPrint()
	rp.print(textbox.insertPlainText, 'Hola mundo!')
	win.show()
	app.exec_()
