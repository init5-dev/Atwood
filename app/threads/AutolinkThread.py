from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
import app.packages.myutils as mu
from app.packages.autolink2 import Autolink
import sys, markdown as md, openai

class AutolinkThread(QThread):
	
	message = pyqtSignal(str)
	link = pyqtSignal(str, str)
	finished = pyqtSignal(str)
	error = pyqtSignal(str)
	stopped = pyqtSignal(str)

	def __init__(self, parent, apikey, text, data):

		super(AutolinkThread, self).__init__(parent)
		self.text = mu.fix_markdown_line_breaks(text).strip()
		self.data = data
		self.autolink = Autolink(apikey)
		self._stop = False
		self.links = []

	def cancellate(self):
		self._stop = True
		self.autolink.stop()
		#print('CANCELADO AUTO ENLAZADO')

	@pyqtSlot(str)
	def __insertLinks(self):

		if not len(self.text):
			print('El texto esta vacio')
			return self.text

		#print('INTENTANDO ENLACES EN:\n%s' % text)
		elements = self.text.strip().split('\n\n')
		elength = len(elements)

		if elength:

			linkedText = '' 
			title = ''

			for i in range(0, elength):
				#print('%s: %s' % (i, elements[i]))

				if '[h1]:' in elements[i]:

					title = elements[0].replace('#', '').strip()
					#print('El titulo es: ' + title)
					linkedText = linkedText + elements[i] + '\n\n'
					continue

				elif '**Metadescripción:**' in elements[i]:
					linkedText = linkedText + elements[i] + '\n\n'
					continue

				self.message.emit('Buscando frases para enlazar.')

				if not len(title):
					title = elements[i]

				try:

					for chunk in self.autolink.links(
														title, 
														elements[i],
														num=self.data['alconf']['num'], 
														stop=self.data['alconf']['stop'], 
														tld=self.data['alconf']['tld'], 
														pause=self.data['alconf']['pause'], 
														delay=self.data['alconf']['delay'], 
														min_kwords=self.data['alconf']['min_kw'], 
														max_kwords=self.data['alconf']['max_kw']
													):

						if self._stop:
							self.stopped.emit()
							break

						if chunk[0] == 'message':
							self.message.emit(chunk[1])
						else:
							term = chunk[1]
							a = chunk[2]
							
							if not (term in self.links):
								elements[i] = elements[i].replace(term, a, 1) + '\n\n'
								self.message.emit('Enlace generado. Buscando más frases para enlazar.')
								self.links.append(term)

				except openai.error.APIError as e:
					self.error.emit("Error de OpenAI. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.")
					return
				except openai.error.Timeout as e:
					self.error.emit("Tiempo de espera agotado. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.")
					return
				except openai.error.RateLimitError as e:
					self.error.emit("Cuota excedida. Comprueba tu plan y detalles de facturación en https://platform.openai.com/account/.")
					return
				except openai.error.APIConnectionError as e:
					self.error.emit("Por favor, asegúrate de que tienes conexión a Internet.")
					return
				except openai.error.InvalidRequestError as e:
					self.error.emit("¡GPT no entendió uno de los datos que le proporcionaste. Por favor, revisa la información que introduciste, especialmente la del índice.")
					return
				except openai.error.AuthenticationError as e:
					self.error.emit("API key incorrecta. Busca tu API key en https://platform.openai.com/account/api-keys y regístrala aquí en Atwood.")
					return
				except openai.error.ServiceUnavailableError as e:
					self.error.emit('¡El servidor está sobrecargado! Inténtalo más tarde. Y, si estás usando la prueba gratuita de GPT, es buena idea adquirir un plan de pago.')
					return
				except Exception as e:
					self.error.emit('ERROR EN ArticleThread: %s' % str(e))
					excinfo = sys.exc_info()
					#print('EXCINFO IN ARTICLE WRITER: %s' % excinfo)
					return

				linkedText = linkedText + elements[i] + '\n\n'
		#print('EL TEXTO LINKEADO ES:\n%s' % linkedText)
		return linkedText
			

	def run(self):

		self.message.emit('Buscando frases para enlazar.')
		
		linkedContent = self.__insertLinks()

		if not linkedContent:
			return

		html = md.markdown(linkedContent)
		#print('EL HTML ES:\n%s' % html)
		self.finished.emit(html)