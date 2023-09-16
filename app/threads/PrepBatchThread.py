from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from app.packages.atengine.atwriter import AtWriter
import openai, copy, time, sys, markdown as md

class PrepBatchThread(QThread):

	error = pyqtSignal(str)
	msg = pyqtSignal(str)
	title = pyqtSignal(str)
	checks = pyqtSignal(bool)
	newIndex = pyqtSignal(list)
	finished = pyqtSignal(list)

	def __init__(self, parent, apikey, keywords, data, fast_testing_mode):
		super(PrepBatchThread, self).__init__(parent)
		self.apikey = apikey
		self.keywords = keywords
		self.data = data
		self.fast_testing_mode = fast_testing_mode
		self._stop = False

	def cancellate(self):
		self._stop = True

	@pyqtSlot(str)
	def run(self):

		indexWriter = AtWriter(apikey=self.apikey)
		try:

			bdata = []

			for entry in self.keywords:

				if self._stop:
					break

				#entry = entry.capitalize()
				self.title.emit(entry)
				self.data['scope'] = entry
				self.data['fast_testing_mode'] = self.fast_testing_mode
				
				if not self.data['small-entry']:
					self.msg.emit('Generando índice para "%s".' % entry)
					self.data['index'] = indexWriter.suggestIndex(
														self.data['scope'], 
														self.data['reader'], 
														self.data['style']
													).strip().splitlines()
				else:
					self.data['index'] = []
				
				self.newIndex.emit(self.data['index'])

				if len(self.data['index']) == 1 and not self.data['auto-intro']:
					self.checks.emit(True)
					self.data['auto-intro'] = True

				if len(self.data['index']) == 0:
					self.checks.emit(False)
					self.data['auto-intro'] = False

				bdata.append(copy.deepcopy(self.data))
				time.sleep(0.1)

			self.finished.emit(bdata)
		
		except openai.error.APIError as e:
			self.error.emit("Error de OpenAI. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.")
		except openai.error.Timeout as e:
			self.error.emit("Tiempo de espera agotado. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.")
		except openai.error.RateLimitError as e:
			self.error.emit("Cuota excedida. Comprueba tu plan y detalles de facturación en https://platform.openai.com/account/.")
		except openai.error.APIConnectionError as e:
			self.error.emit("Por favor, asegúrate de que tienes conexión a Internet.")
		except openai.error.InvalidRequestError as e:
			self.error.emit("¡GPT no entendió uno de los datos que le proporcionaste. Por favor, revisa la información que introduciste, especialmente la del índice.")
		except openai.error.AuthenticationError as e:
			self.error.emit("API key incorrecta. Busca tu API key en https://platform.openai.com/account/api-keys y regístrala aquí en Atwood.")
		except openai.error.ServiceUnavailableError as e:
			self.error.emit('¡El servidor está sobrecargado! Inténtalo más tarde. Y, si estás usando la prueba gratuita de GPT, es buena idea adquirir un plan de pago.')
		except Exception as e:
			self.error.emit('ERROR EN PrepBatchThread: %s' % str(e))