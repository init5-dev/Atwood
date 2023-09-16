from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import time

class MessageLoopThread(QThread):

	clean = pyqtSignal()
	update = pyqtSignal(str) 
	finished = pyqtSignal()

	def __init__(self, parent, message, delay = 0.1):
		super(MessageLoopThread, self).__init__(parent)
		self.message = message
		self.delay = delay
		self._stop = False

	def cancellate(self):
		self._stop = True

	@pyqtSlot()
	def run(self):

		dots = 1
		print(f"MESSAGE: {self.message}")

		while not self._stop:
			if dots > 3:
				dots = 0
			self.clean.emit()
			line = '<p style="color:#3EB489"><i>%s%s</i></p>' % (self.message, '.' * dots)
			self.update.emit(line)
			dots += 1
			time.sleep(self.delay)

		self.finished.emit()
		#print('MESSAGE THREAD IS FINISHED')