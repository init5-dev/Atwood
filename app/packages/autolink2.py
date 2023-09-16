import openai
import googlesearch as gs
import copy
import time
import urllib
from urllib.parse import unquote
import secret as secret
from colorama import Fore
from PyQt5.QtWidgets import *


class Autolink:

	def __init__(self, apikey, exclude_terms = []):
		self.apikey = apikey
		openai.api_key = self.apikey
		self._stop = False
		self.exclude_terms = exclude_terms
		self.retries = 6
		self.retryNumber = 0
		self.errorWaiting = 10
		self.searchTry = 0
		self.searchTries = 3
		self.searchWaiting = 60

	def stop(self):
		print('=> Autolink.stop()')
		self._stop = True

	def inScope(self, term, scope):
		comando = 'Responde "Sí" si el término "{}" pertenece al tema "{}"; de lo contrario, responde "No"'.format(term, scope)
		result = self.answer(comando)
		#print(result)
		if result.find('Sí') > -1:
			return True
		return False

	def getNiche(self, scope):

		comando = '''
El título o tema "{}" pertenece a la siguiente categoría o subcategoría temática específica: 
'''.format(scope)
		result = self.answer(comando)
		#print('TITULO: %s | NICHO: %s' % (scope, result))
		return result

	def __get_response(self, prompt, model='gpt-3.5-turbo', temperature=0, top_p=0, presence_penalty=0, frequency_penalty=0, max_tokens=40):
		return openai.ChatCompletion.create(
				model = model,
				messages = [
							{'role':'system', 'content':'Responde de la manera más concisa posible.'}, 
							{'role':'user', 'content' : prompt}
						   ],
				temperature = temperature,
				top_p = top_p,
				presence_penalty = presence_penalty,
				frequency_penalty = frequency_penalty,
				max_tokens = max_tokens			
				)

	def answer(self, prompt, model='gpt-3.5-turbo', temperature=0, top_p=0, presence_penalty=0, frequency_penalty=0, max_tokens=40):
		#print(prompt)
		answer = ''

		try:
			response = self.__get_response(prompt, model, temperature, top_p, presence_penalty, frequency_penalty, max_tokens)	
		except openai.error.APIConnectionError as e:
			self.retryNumber += 1
			if self.retryNumber <= self.retries:
				print('No se pudo conectar con OpenAI. Intentado en %s segundos...' % self.errorWaiting)
				time.sleep(self.errorWaiting)
				answer = self.answer(prompt, temperature, top_p, presence_penalty, frequency_penalty, max_tokens)
				if answer:
					return answer.strip()

				return ''
			else:
				print('Intentos de conectar con OpenAI fallidos.')
				self.retryNumber = 0
				raise e 

		#print(response)
		answer = answer + response['choices'][0]['message']['content']
		if answer:
			return answer.strip()

		return ''

	def __split_into_sentences(self, text):
		command = f'''
Divide en oraciones el siguiente texto: \"{text}\". El formato de respuesta es: 

Lista de oraciones sin viñetas ni numeración.

'''
		sentences = self.answer(command, max_tokens=750).splitlines()
		return sentences


	def entities(self, text):
		#print(f"El texto es '{text}'")

		if not len(text.strip()):
			return ''
	
		nouns = []
		sentences = self.__split_into_sentences(text)
		for sentence in sentences:
			command = f'''
Te proporcionare el siguiente texto:

"""
{sentence}
""" 

Respuesta:
Lista de entidades semánticas presentes en el texto.

'''	
			print(f"ORACION: {sentence}")
			ents = self.answer(command, temperature=0.5, max_tokens=150).splitlines()
			tmp = []
			for ent in ents:
				tmp.append(ent.replace('-', '', 1).strip())

			print(f"ANCHOR: {tmp}")
			nouns += tmp
		return nouns																			

	def search(self, term, site='', tld="co.in", num=10, stop=10, pause=2):
		results = []
		
		try: 

			query = f"{term} site: {site}" if len(site) else term
			yield 'msg', f"Buscando '{term}' in Google... "
			
			searchGen = gs.search(query, tld=tld, num=num, stop=stop, pause=pause)
				
			while not self._stop:

				try:
					result = searchGen.__next__() 
				except StopIteration:
					break
				
				yield 'msg', 'URL encontrada: ' + result
				yield 'res', result
				results.append(result)

		except urllib.error.HTTPError as e:

			self.searchTry += 1

			if self.searchTry <= self.searchTries:

				if self._stop:
					print('Detenido metodo search() en recuperacion del urllib.error.HTTPError')
					return []

				yield 'msg', 'Muchas solicitudes. Se esperara %s segundos para reintentar.' % self.searchWaiting
				time.sleep(self.searchWaiting)
				return self.search(term, tld, num, stop, pause)
			else:
				self.searchTry = 0
				yield 'err', 'Fallaron los intentos por exceso de solicitudes. Intentalo mas tarde.'
				raise e
			
		except Exception as e:

			yield 'err', 'ERROR EN AUTOLINK. SEARCH(): ' + str(e)
			raise e
		
		return results

	def inSlug(self, term, url, coincidence=0.75):
		try:
			encoded_url = unquote(url)
		except Exception as e:
			print(url)
			return
		#print('ENCODED URL: ' + encoded_url)
		keywords = term.lower().split(' ')
		slug = encoded_url[encoded_url.find('/')+1:]
		skeywords = slug.replace('/','-').replace(':', '-').replace('.', '-').replace('--', '-').replace('---', '-').split('-')
		count = 0
		for keyword in keywords:
			if keyword in skeywords:
				count += 1
		return count >= coincidence * len(keywords)
	
	def textlinks(self, text : str, sites : list, num=20, stop=20, tld='co.in', pause=2, delay=2):
		ents = self.entities(text, 1, 6)
		logblock('ENTIDADES:', ents)
		
		links = []
		kwlinksGen = self.kwlinks(ents, sites, num, stop, tld, pause, delay)
		while not self._stop:	

			try:
				chunk = kwlinksGen.__next__() 
			except StopIteration:
				break
		
			if chunk[0] == 'res':
				links.append(chunk[1])
			yield chunk

		return links
	
	def kwlinks(self, keywords : list, sites : list, num=20, stop=20, tld='co.in', pause=2, delay=2):

		links = []

		if not len(sites):
			sites = ['']

		keywordsGen = keywords.__iter__()
		sitesGen = sites.__iter__()

		while not self._stop:

			try:
				keyword = keywordsGen.__next__()
			except StopIteration:
				break

			while not self._stop:

				try:
					site = sitesGen.__next__()					 
				except StopIteration:
					break

				results = []

				searchGen = self.search(keyword, site)

				while not self._stop:

					try:
						chunk = searchGen.__next__() 
					except StopIteration:
						break
								
					if chunk[0] == 'res':
						yield 'msg', 'Procesando resultado: ' + chunk[1]
					
						if self.inSlug(keyword, chunk[1], 0.25):
							link = '<a href="%s">%s</a>' % (chunk[1], keyword)
							yield 'res', (keyword, link)
							links.append((keyword, link))
							yield 'msg', 'Creado enlace: ' +  link
					else:
						yield chunk

				time.sleep(delay)

		return links
	
	def links(self, title, text, num=20, stop=20, tld='co.in', pause=2, delay=2, min_kwords=1, max_kwords=6):
		links = []
		print('Obteniendo sintagmas...')
		nphrases = self.entities(text)
		print(f"SINTAGMAS:")
		nouns = set([nphrase.strip() for nphrase in nphrases])
		for n in nouns:
			print(f"\t{n}")
		print('Obteniendo ámbito temático...')
		scope = self.getNiche(title)

		if scope == '#Ninguna;':
			#print('La categoría tematica es #Ninguna;')
			return []

		print('Obteniendo enlaces...')
		for noun in nouns:

			if self._stop:
				return []

			if self.inScope(noun, scope):

				if self._stop:
					return []

				#yield ['message', 'Intentado generar un enlace para "%s".' % noun]

				search_term = '%s %s' % (noun, scope)
				
				for result in self.search(search_term, tld=tld, num=num, stop=stop, pause=pause):

					if self._stop:
						return []

					if result[0] != 'res':
						continue

					url = result[1]
					print("URL: " + url)

					if self.inSlug(noun, url):
						#print('ENLACE OBTENIDO: <a href="%s">%s</a>' % (result, nphrase))
						link = '<a href="%s">%s</a>' % (url, noun)
						links.append(link)
						yield ['result', noun, link]
						break
				time.sleep(delay)

		return links

def log(message, tabs = 0):
	tabulation = '\t' * tabs
	print(f"{tabulation}{Fore.BLUE}{message}")
	return f"{tabulation}{message}"

def logvar(name, value, tabs = 0):
	tabulation = '\t' * tabs
	print(f"{tabulation}{Fore.BLUE}{name}{Fore.WHITE} = {Fore.LIGHTYELLOW_EX}{value}{Fore.WHITE}")
	return f"{tabulation}{name} = {value}"

def logblock(name, value, tabs = 0, tabulate_value=True):
	tabulation = '\t' * tabs
	innerTabulation = tabulation + '\t'
	print(f"{tabulation}{Fore.BLUE}{name}{Fore.WHITE}:\n{innerTabulation}{Fore.LIGHTYELLOW_EX}{value}{Fore.WHITE}")
	return f"{tabulation}{name}:\n{innerTabulation}{value}"

if __name__ == "__main__":
	alink = Autolink("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")
	title = "Qué es ChatGPT"
	text = '''
ChatGPT es un sistema de chat basado en el modelo de lenguaje por Inteligencia Artificial GPT-3.5, desarrollado por la empresa OpenAI. Es un modelo con más de 175 millones de parámetros, y entrenado con grandes cantidades de texto para realizar tareas relacionadas con el lenguaje, desde la traducción hasta la generación de texto.

Realmente, ChatGPT tiene dos versiones diferentes. Tienes la versión gratuita con GPT-3.5, pero también tienes una versión de pago llamada ChatGPT Plus, y que cuenta con un GPT-4 más moderno y avanzado. Este modelo también lo encuentras en alternativas gratuitas como Bing Chat.

A una inteligencia artificial se la entrena a base de texto, se le hacen preguntas y se le añade información, de manera que este sistema, a base de correcciones a lo largo del tiempo, va "entrenándose" para realizar de forma automática la tarea para la que ha sido diseñada. Este es el método para entrenar a todas las IA, tanto a la de ChatGPT como otras del estilo de los Magic Avatars de Lensa.

'''
	links = alink.links(title, text)
	for link in links:
		print(link)