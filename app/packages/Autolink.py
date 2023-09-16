import openai
import googlesearch as gs
import spacy
import copy
import time
import urllib
from urllib.parse import unquote
import app.packages.secret as secret
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

	def __get_response(self, prompt, temperature=0, top_p=0, presence_penalty=0, frequency_penalty=0, max_tokens=40):
		return openai.ChatCompletion.create(
				model = 'gpt-3.5-turbo',
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

	def answer(self, prompt, temperature=0, top_p=0, presence_penalty=0, frequency_penalty=0, max_tokens=40):
		#print(prompt)
		answer = ''

		try:
			response = self.__get_response(prompt, temperature, top_p, presence_penalty, frequency_penalty, max_tokens)	
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
		sentences = self.answer(
f'''Divide en oraciones el siguiente texto: \"{text}\". El formato de respuesta es: 

### ORACIONES:
oración 1
oración 2
...
oración n

'''
			)
		print(sentences)

	def ___split_into_sentences(self, text):
		nlp = spacy.load('es_core_news_sm')
		doc = nlp(text)
		sentences = []

		for sent in doc.sents:
			start = sent.start
			end = sent.end

			if (sent.text[-1] == "!" or sent.text[-1] == "?") and len(sentences) > 0:
				last_sent_end = sentences[-1][1]

				if last_sent_end < start:
	                # Add any missing punctuation at the end of previous sentence
					prev_sent_text_without_punct = doc[last_sent_end:start].text.strip()
					prev_sent_text_with_punct = prev_sent_text_without_punct + sent.text[-1]
					sentences[-1] = (sentences[-1][0], start + len(prev_sent_text_with_punct) - 2)

	            # Include current exclamation/interrogation sentence as its own separate sentence
				sentences.append((start, end))
			else:
	            # Append regular sentence to list
				sentences.append((start, end))

		return [doc[start:end].text for start,end in sentences]

	def __is_valid_ent(self, e, no_misc = False):
		'''
		PERSON - People, including fictional.

NORP - Nationalities or religious or political groups.

FAC - Buildings, airports, highways, bridges, etc.

ORG - Companies, agencies, institutions, etc.

GPE - Countries, cities, states.

LOC - Non-GPE locations, mountain ranges, bodies of water.

PRODUCT - Objects, vehicles, foods, etc. (Not services.)

EVENT - Named hurricanes, battles, wars, sports events, etc.

WORK_OF_ART - Titles of books, songs, etc.

LAW - Named documents made into laws.

LANGUAGE - Any named language.

DATE - Absolute or relative dates or periods.

TIME - Times smaller than a day.

PERCENT - Percentage, including "%".

MONEY - Monetary values, including unit.

QUANTITY - Measurements, as of weight or distance.

ORDINAL - "first", "second", etc.

CARDINAL - Numerals that do not fall under another type.'''
		
		#print('E: %s | LABEL: %s' % (e.text, e.label_), end= ' ')

		if not no_misc:
			eTypes = ["PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "LANGUAGE", "MISC"]
		else:
			eTypes = ["PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "LANGUAGE"]

		#print(eTypes)

		if e.label_ in eTypes and e.text.find('<') == -1 and e.text.find('>') == -1:
			#print('IS TRUE')
			return True
		else:
			#print()
			return False

	'''- "ADJ": Adjective
- "ADP": Adposition (e.g. preposition, postposition)
- "ADV": Adverb
- "AUX": Auxiliary verb
- "CONJ": Conjunction
- "CCONJ": Coordinating conjunction
- "DET": Determiner (e.g. article, demonstrative pronoun)
- "INTJ": Interjection
- "NOUN": Noun
- "NUM": Numeral
- "PART": Particle (e.g. negation particle, infinitival to)
- "PRON": Pronoun
- "PROPN": Proper noun
- "PUNCT": Punctuation mark
- "SCONJ" Subordinating conjunction'''

	def getEntitiesThroughGpt(self, text):
		#print(f"El texto es '{text}'")

		if not len(text.strip()):
			return ''
		
		command = f'''
Te proporcionare el siguiente texto:

"""
{text}
""" 

Del texto proporcionado, extrae un sintagma que sirva de candidato para crear un enlace. Responde estricamente usando la siguiente sintaxis:

#ANCHOR TEXT: <sintagma>

'''
		ans = self.answer(command, temperature=0.5, max_tokens=150)
		print(f"La respuesta es: {ans}")
		if "#ANCHOR TEXT:" in ans:
			result = ans.split('#ANCHOR TEXT:')[1]
		else:
			result = ans
		print('EL ANCHOR ES: ' + str(result))
		return result
	
	def entities(self, text, min_kwords = 1, max_kwords=6, use_gpt=True):

		if not use_gpt:
			nlp = spacy.load('es_core_news_sm')
		candidates = []

		sentences = self.__split_into_sentences(text)
		for s in sentences:
			#print('SENTENCE: %s' % s)

			if self._stop:
				print('Detenido metodo entities() en bucle de nivel 1')
				return []

			if use_gpt:
				candidates = candidates + self.getEntitiesThroughGpt(s).split(',')
			else:
			
				sdoc = nlp(s)
				first = True

				for e in sdoc.ents:

					if self._stop:
						print('Detenido metodo entities() en bucle de nivel 2')
						return []
			
					if self.__is_valid_ent(e) and not (e.text in self.exclude_terms):
						words = e.text.split()
						size = len(words)
						if size >= min_kwords and size <= max_kwords:
							candidates.append(e.text)

				forbidden_pos = [
									"ADP",
									"ADV",
									"AUX",
									"CONJ",
									"CCONJ",
									"DET",
									"INTJ",
									"NUM",
									"PART",
									"PRON",
									"PUNCT",
									"SCONJ",
									"VERB",
									"SYM"
								]
				first = True

				for np in sdoc.noun_chunks:

					if self._stop:
						print('Detenido metodo entities() en bucle de nivel 2')
						return []
					
					if first:
						first = False
						continue

					if np.text in self.exclude_terms:
						continue

					words = np.text.split()
					size = len(words)

					if "http" not in np.text and size >= min_kwords and size <= max_kwords and np.text.find('<') == -1 and np.text.find('>') == -1:

						if len(words):
							if (size == 1 and np[0].text.split()[0].isupper() and np[0].pos_ != 'PROPN'):
								continue
							if (size == 1 and np[0].text.split()[0].islower()):
								continue
							candidate = True
							nouns = 0
							for npe in np: 
								if npe.pos_ == 'NOUN' or npe.pos_ == 'PROPN':
									nouns += 1

								if npe.pos_ in forbidden_pos:
									candidate = False

							candidate = candidate and nouns > 0

							if candidate:	
								candidates.append(np.text)

		cleanedList = list(set(candidates))
		result = copy.deepcopy(cleanedList)

		return result																			

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
		encoded_url = unquote(url)
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
		nphrases = self.entities(text, min_kwords=min_kwords, max_kwords=max_kwords)
		scope = self.getNiche(title)

		if scope == '#Ninguna;':
			#print('La categoría tematica es #Ninguna;')
			return []

		print('Obteniendo enlaces...')
		for nphrase in nphrases:

			if self._stop:
				return []

			if self.inScope(nphrase, scope):

				if self._stop:
					return []

				#yield ['message', 'Intentado generar un enlace para "%s".' % nphrase]

				search_term = '%s %s' % (nphrase, scope)
				results = self.search(search_term, tld=tld, num=num, stop=stop, pause=pause)
				
				for result in results:

					if self._stop:
						return []

					if self.inSlug(nphrase, result):
						#print('ENLACE OBTENIDO: <a href="%s">%s</a>' % (result, nphrase))
						link = '<a href="%s">%s</a>' % (result, nphrase)
						links.append(link)
						yield ['result', nphrase, link]
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
	alink.__split_into_sentences("Hola, me llamo Nelson. ¿Cuál es tu nombre?")