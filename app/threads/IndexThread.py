from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from app.packages.atengine.atwriter import AtWriter
import openai

class IndexThread(QThread):

	error = pyqtSignal(str)
	finished = pyqtSignal(list)

	def __init__(self, parent, apikey, idata):
		super(IndexThread, self).__init__(parent)
		self.apikey = apikey
		self.idata = idata
		#print('INDEX DATA %s ' % self.idata)

	def cancellate(self):
		self.quit()
		self.wait()

	@pyqtSlot(list)
	def run(self):

		indexWriter = AtWriter(apikey=self.apikey)
		try:

			index = indexWriter.suggestIndex(
												self.idata['scope'], 
												self.idata['reader'], 
												self.idata['style']
											).strip().splitlines()

			self.finished.emit(index)
		
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
		#except Exception as e:
			self.error.emit('ERROR EN IndexThread: %s' % str(e))