import re
import keyutils.secret as ks

from colorama import Fore

try:
	from atwriter import AtChat
except:
	from app.packages.atengine.atwriter import AtChat

try:
	from atwriter import AtWriter
except:
	from app.packages.atengine.atwriter import AtWriter

#***********************************************************
#UTILS
#***********************************************************

def remove_html_tags(text):
	clean = re.compile('<.*?>')
	return re.sub(clean, '', text)

#***********************************************************
#CLASSES
#***********************************************************
class GptRebelionException(Exception):
	pass

class AtResearcher:

	def __init__(self, apikey, verbose=False):
		self.apikey = apikey
		self.verbose = verbose
		
	def readHtml(html):
		text = remove_html_tags(html)
		print(f"{Fore.GREEN}TEXTO EXTRAIDO")
		return text

	def sumarize(self, text):
		command = f'''
Sigue estrictamente mis instrucciones. Lee el siguiente texto y resúmelo en forma de una lista que contenga las ideas y datos principales. El formato de tu respuesta tiene que ser el siguiente:

#LISTA-RESUMEN:
<elemento 1>
<elemento 2>
...
<elemento n>

A continuación, te proporciono el texto a resumir según las instrucciones especificadas:

{text}
		'''
		atc = AtChat(self.apikey)
		answer = ''
		for chunk in atc.answer(command):
			if chunk:
				answer = answer + chunk
				if self.verbose:
					print(chunk, end='')
		if self.verbose:
			print('')

		return answer.split('#LISTA-RESUMEN:')[1].strip()
	
	def write(self, summaries):
		for summary in summaries:
			command = f'''
Sigue estrictamente mis instrucciones:

1. Escribe un texto nuevo y creativo basado en la información contenida en la siguiente lista:

	{summary}

2. Proporcióname dicho texto en el siguiente formato:

#TEXTO:
<el artículo que escribiste en forma markdown(usando la sintaxis de GitHub)>
			'''

			atc = AtChat(self.apikey)
			text = ''

			for chunk in atc.answer(command):
				if chunk:
					text = text + chunk
					if self.verbose:
						print(chunk, end='')
			if self.verbose:
				print('')

			content = text.split('#TEXTO:')
			if len(content) > 1:
				return content[1].strip()
			else:
				exc_message = f"{Fore.RED} ERROR: GPT RESPONDIÓ:{Fore.WHITE}\n\ntext\n"
				raise GptRebelionException(exc_message)
	
if __name__ == '__main__':
	mistery = 'ep-k9CZ0JPRWKgiz1xil0jZNkls5SIuR87XgNN6ZuN4=' #clave para guardar y leer la API key de OpenAI
	apikey = ks.read_file(mistery, './api.key')
	text = '''
<p>Una interfaz de programa de aplicación (API) define las reglas que se deben seguir para comunicarse con otros sistemas de software. Los desarrolladores exponen o crean API para que otras aplicaciones puedan comunicarse con sus aplicaciones mediante programación. Por ejemplo, la aplicación de planilla de horarios expone una API que solicita el nombre completo de un empleado y un rango de fechas. Cuando recibe esta información, procesa internamente la planilla de horarios del empleado y devuelve la cantidad de horas trabajadas en ese rango de fechas.</p>

<p>Se puede pensar en una API web como una puerta de enlace entre los clientes y los recursos de la Web.</p>

<h3>Clientes</h3>
<p><p>Los clientes son usuarios que desean acceder a información desde la Web. El cliente puede ser una persona o un sistema de software que utiliza la API. Por ejemplo, los desarrolladores pueden escribir programas que accedan a los datos del tiempo desde un sistema de clima. También se puede acceder a los mismos datos desde el navegador cuando se visita directamente el sitio web de clima.</p>

<h3>Recursos</h3>
Los recursos son la información que diferentes aplicaciones proporcionan a sus clientes. Los recursos pueden ser imágenes, videos, texto, números o cualquier tipo de datos. La máquina encargada de entregar el recurso al cliente también recibe el nombre de servidor. Las organizaciones utilizan las API para compartir recursos y proporcionar servicios web, a la vez que mantienen la seguridad, el control y la autenticación. Además, las API las ayudan a determinar qué clientes obtienen acceso a recursos internos específicos.</p>
	'''
	atr = AtResearcher(apikey)
	summary = atr.sumarize(text)
	article = atr.write([summary])
	
	print(f"{Fore.GREEN}SUMARIO:{Fore.WHITE}\n\n{summary}\n")
	print(f"{Fore.GREEN}TEXTO:{Fore.WHITE}\n\n{article}")
		