from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from app.packages.atengine.atwriter import AtWriter
from app.packages.autolink2 import Autolink
from colorama import Fore
import app.packages.myutils as mu
import openai, time

class ArticleThread(QThread):
	
	writerSignal = pyqtSignal(AtWriter)
	message = pyqtSignal(str)
	text = pyqtSignal(str)
	ltext = pyqtSignal(str)
	link = pyqtSignal(str, str)
	finished = pyqtSignal()
	error = pyqtSignal(str, AtWriter, dict)
	stopped = pyqtSignal(AtWriter, dict)

	def __init__(self, parent, apikey, data=None, recuperate=None):

		super(ArticleThread, self).__init__(parent)
		self.data = data
		#print('RECUPERATE IN ARTICLE THREAD: %s' % recuperate)
		if not recuperate:
			self.writer = AtWriter(apikey=apikey, autoIntro = data['auto-intro'], metadescription = data['meta'], verbose = False)
			self.writer.setModel(data['writer']['engine'])
			self.writer.setRetries(data['writer']['retries'])
			self.writer.setLatency(data['writer']['latency'])
			self.writer.setRetriesAfterError(data['writer']['retries_after_error'])
			self.writer.setErrorLatency(data['writer']['error_latency'])
			self.writer.temperature = data['writer']['temperature']
			self.writer.topP = data['writer']['top_p']
			self.writer.frequencyPenalty = data['writer']['frequency_penalty']
			self.writer.presencePenalty = data['writer']['presence_penalty']
			self.writer.maxTokens = data['writer']['max_tokens']
		else:
			#print('ARTICLED THREAD RUNNING IN RECUPERATION MODE.')
			self.writer = recuperate

		self.writer.fast_testing_mode(data['fast_testing_mode'])

		print('SE USARÁ EL MODELO %s' % self.writer.model)
		self.links = [] #registro para no repetir enlaces
		self.autolink = Autolink(apikey, self.links)
		self._stop = False
		self.title = ''
		self.printQueue = []
		print('FAST TESTING MODE: %s' % self.writer._fast_testing_mode)

	def cancellate(self):
		self.writer.cancellate()
		self._stop = True

	def __insertLinks(self, text):

		if not len(text.strip()):
			#print('El texto esta vacio')
			return text

		self.message.emit('Sección escrita. Buscando frases para enlazar.')

		for chunk in self.autolink.links(
											self.title, 
											text,
											num=self.data['alconf']['num'], 
											stop=self.data['alconf']['stop'], 
											tld=self.data['alconf']['tld'], 
											pause=self.data['alconf']['pause'], 
											delay=self.data['alconf']['delay'], 
											min_kwords=self.data['alconf']['min_kw'], 
											max_kwords=self.data['alconf']['max_kw']
										):

			if self._stop:
				self.stopped.emit(self.writer, self.data)
				print(f"{Fore.RED}ARTICLE WRITER INSERTING LINKS STOPPED.")
				return text

			if chunk[0] == 'message':
				self.message.emit(chunk[1])
			else:
				term = chunk[1]
				a = chunk[2]
						
				if not (term in self.links):
					text = text.replace(term, a, 1)
					self.links.append(term)

		return text
			
	#@pyqtSlot()
	def run(self):

			try:
				self.writerSignal.emit(self.writer)
				for chunk in self.writer.article(
							self.data['scope'],
							self.data['author'],
							self.data['style'],
							self.data['reader'],
							self.data['extra'],
							self.data['index'],
							self.data['wait']
						):
					#print('CHUNK: %s' % chunk)
					if self._stop:
						print('ESCRITURA DETENIDA!')
						self.stopped.emit(self.writer, self.data)
						return

					#Si hay un nuevo error
					if len(self.writer.printQueue) > len(self.printQueue):
						lprint = self.writer.getLastPrint()
						self.message.emit(lprint)
						self.printQueue.append(lprint)

					if chunk['type'] == 'message':
						self.message.emit(chunk['content'])
						#print(chunk['content'])
					else:

						if chunk['content']['title'].find('<h1') != -1:
							self.title = mu.remove_html_tags(chunk['content']['title'])

						if self.data['autolink']:

							if not ('id="meta"' in chunk['content']['body']):
								linkedText = self.__insertLinks(chunk['content']['body'])
							else:
								linkedText = chunk['content']['body']

						entry = {
									'title' : chunk['content']['title'], 
									'content': linkedText if self.data['autolink'] else chunk['content']['body']
								}


						if len(entry['title']):
							if entry['title'].find('<h2') != -1:
								contTitle = ('<p style="font-size:x-large; font-weight:600"><span>[h2]: %s</span></p>\n' % mu.remove_html_tags(entry['title']))
							elif entry['title'].find('<h1') != -1:
								if self.data['show-title']:
									contTitle = ('<h1>[h1]: %s</h1>' % mu.remove_html_tags(entry['title']))
								else:
									contTitle = ''
							else:
								contTitle = entry['title']
						else:
							contTitle = ''

						textSignal = '%s%s<br>' % (contTitle, mu.insert_missing_close_tags(entry['content']))
						self.text.emit(textSignal)
						#print(f"EMITIDO: { textSignal }")

					time.sleep(0.1)

				print('ESCRITURA TERMINADA!')
				self.finished.emit()

			except openai.error.APIError as e:
				self.error.emit("Error de OpenAI. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.", self.writer, self.data)
				return
			except openai.error.Timeout as e:
				self.error.emit("Tiempo de espera agotado. Espera unos minutos e inténtalo de nuevo. Si el problema persiste, contacta con la empresa.", self.writer, self.data)
				return
			except openai.error.RateLimitError as e:
				self.error.emit("Cuota excedida. Comprueba tu plan y detalles de facturación en https://platform.openai.com/account/.", self.writer, self.data)
				return
			except openai.error.APIConnectionError as e:
				self.error.emit("Por favor, asegúrate de que tienes conexión a Internet.", self.writer, self.data)
				return
			except openai.error.InvalidRequestError as e:
				self.error.emit("¡GPT no entendió uno de los datos que le proporcionaste. Por favor, revisa la información que introduciste, especialmente la del índice.", self.writer, self.data)
				return
			except openai.error.AuthenticationError as e:
				self.error.emit("API key incorrecta. Busca tu API key en https://platform.openai.com/account/api-keys y regístrala aquí en Atwood.", self.writer, self.data)
				return
			except openai.error.ServiceUnavailableError as e:
				self.error.emit('¡El servidor está sobrecargado! Inténtalo más tarde. Y, si estás usando la prueba gratuita de GPT, es buena idea adquirir un plan de pago.', self.writer, self.data)
				return
			except Exception as e:
				self.error.emit('ERROR EN ArticleThread: %s' % str(e), self.writer, self.data)
				#excinfo = sys.exc_info()
				#print('EXCINFO IN ARTICLE WRITER: %s' % excinfo)
				return