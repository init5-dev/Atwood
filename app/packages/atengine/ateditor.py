from atchat import AtChat

class AtEditor(AtChat):
	def __init__(self, article, paragraphsMemory = 3):
		super().__init__()
		self.temperature=0
		self.frequencyPenalty=0
		self.presencePenalty=0
		self.maxTokens=1000
		self.topP=0.25
		systemContent='Sigue estrictamente mis órdenes: a partir de ahora, simula que no eres un chatbot, sino una implementacion del modelo text-davinci-003 que se dedica a la correccion y mejora de textos.'
		self.messages = [{'role':'system', 'content':systemContent}]
		self.article = article
		self.last = ''
		self.printQueue = []
		self.paragraphsMemory = paragraphsMemory

	def resetMessages(self):
		self.messages = [self.messages[2]]

	def removeHtmlTags(self, html):
	    # Remover etiquetas HTML
	    clean_text = re.sub(r'<[^>]+>', '', html)
	    
	    # Remover comentarios HTML
	    clean_text = re.sub(r'<!--.*?-->', '', clean_text, flags=re.DOTALL)
	    
	    return clean_text

	def getParagraphs(self, text):
	    """Recibe un texto y devuelve un array con los párrafos del mismo."""
	    
	    paragraphs = text.split("\n\n")  # Dividir el texto en párrafos mediante el separador "\n\n"
	    
	    return paragraphs

	def getSections(self, text):
	    """Recibe un texto y devuelve un array con los párrafos del mismo."""
	    
	    paragraphs = text.split("\n\n")  # Dividir el texto en párrafos mediante el separador "\n\n"
	    
	    return paragraphs

	def improveText(self, text):
		comando ='Sigue estrictamente mis instrucciones: de ser posible, corrige, enriquece y mejora el siguiente texto: "{}"; y, como respuesta, proporcioname unicamente el resultado, sin comentarios ni acotaciones; no encierres entre comillas el texto.'.format(text.strip())
		#answer = self.answer(comando)
		#comando = 'Si hay algun comentario, extrae el texto aludido en el comentario de la siguiente respuesta de ChatGPT: "{}"; si no hay ningun comentario, responde exactamente lo siguiente:"{}"'.format(answer, text)
		#answer = self.answer(comando)
		return self.answer(comando) + '\n\n'

	def improveArticle(self):
		paragraphs = self.getParagraphs(self.removeHtmlTags(self.article))
		cleanedParagraphs = []

		#descartar parrafos vacios
		for paragraph in paragraphs:
			if len(paragraph.strip()):
				cleanedParagraphs.append(paragraph)

		paragraphs = cleanedParagraphs
		
		#mejorar texto linea por linea
		improvedArticle = ''
		i = 0

		for paragraph in paragraphs:
			editedLine = self.improveText(paragraph)
			print(editedLine)
			improvedArticle = improvedArticle + editedLine
			if i >= self.paragraphsMemory:
				self.resetMessages()
				i = 0
			else:
				i = i+1

		return improvedArticle