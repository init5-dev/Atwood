from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

class FinalizeTasksThread(QThread):
	finished = pyqtSignal()
	removeMsg = pyqtSignal()

	def __init__(self, parent):
		super(FinalizeTasksThread, self).__init__(parent)
		self.parent = parent

	@pyqtSlot()
	def run(self):

		#print('EXECUTING FINALIZE TASKS')

		if self.parent.writingThread:
			if self.parent.writingThread.isRunning():
				self.parent.writingThread.cancellate()
				self.parent.writingThread.wait()

		if self.parent.indexThread:
			if self.parent.indexThread.isRunning():
				self.parent.indexThread.cancellate()
				self.parent.indexThread.wait()

		if self.parent.prepBatchThread:
			if self.parent.prepBatchThread.isRunning():
				self.parent.prepBatchThread.cancellate()
				self.parent.prepBatchThread.wait()

		if self.parent.autolinkThread:
			if self.parent.autolinkThread.isRunning():
				self.parent.autolinkThread.cancellate()
				self.parent.autolinkThread.wait()

		if self.parent.messageThread:
			self.parent.messageThread.cancellate()
			self.parent.messageThread.wait()
			self.removeMsg.emit()

		self.finished.emit()