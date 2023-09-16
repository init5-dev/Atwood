from Responder import *

REPLACE_MARK = '##'
TRUE = '#True;'
FALSE = '#False;'
NULL = '#NULL;'
LANG = 'spanish'

class Doer:

	def __init__(self, apikey):
		self.responder = Responder(apikey)
		self.instructions = []

	def parse(self, instruction: str, args):
		for arg in args:
			instruction = instruction.replace(REPLACE_MARK, arg, 1)
		return instruction

	def parse_quoted(self, instruction: str, args):
		for arg in args:
			instruction = instruction.replace(REPLACE_MARK, f"\"{arg}\"", 1)
		return instruction
	
	def push(self, instruction, args):
		self.instructions.append(self.parse(instruction, args))

	def push_quoted(self, instruction, args):
		self.instructions.append(self.parse_quoted(instruction, args))

	def do(self):
		command = ''
		for instruction in self.instructions:
			command += f"{instruction}\n"
		return self.responder.responde(command)



def configure(apikey, lang='spanish'):
	openai.api_key = apikey
	LANG = lang

def eval(expression, *args):

	if not len(args):
		ans = Responder(openai.api_key).responde(f"{TRUE} if '{expression} else {FALSE}'")
		if ans == TRUE or not FALSE:
			return True
		return False

	for arg in args:
		expression = expression.replace(REPLACE_MARK, f"\"{str(arg)}\"", 1)
	
	return eval(expression)

def ret(expression, *args):
	for arg in args:
		expression = expression.replace(REPLACE_MARK, f"\"{str(arg)}\"", 1)
	return Responder(openai.api_key).responde(expression)

def summarize(text):
	return ret('Summarize ##.', text)

def __remove_puntuation(text):
	text = text.replace('"', '')
	text = text.replace("'", '')
	text = text.replace('.', '')
	text = text.replace(',', '')
	text = text.replace(';', '')
	text = text.replace(':', '')
	return text

def __get(keyphrase, text):
	r = ret(f"{keyphrase.capitalize()}:\n\n{REPLACE_MARK}\n\nIf there is not any of them, answer '{NULL}'.", text).split(', ')
	if len(r) == 1 and r[0] == NULL:
		return []
	tmp = []
	for e in r:
		tmp.append(__remove_puntuation(e))
	return set(tmp)

def verbs(text):
	return __get('verbs', text)

def infinitives(text):
	r = __get('verbs', text)
	inf = []
	for v in r:
		inf.append(ret(f"Infinitive form of: {REPLACE_MARK}.", v, LANG))
	return inf

def nouns(text):
	return __get('nouns', text)

def proper_nouns(text):
	return __get('proper nouns', text)

def common_nouns(text):
	return __get('common nouns', text)

def adjectives(text):
	return __get('adjectives', text)

def by_sentence(text, callback):
	sentences = text.split('.')
	results = []
	for s in sentences:
		r = callback(s)
		results += r
	return results

if __name__ == '__main__':
	apikey = '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'
	#gptdoer = Doer()
	#pinst = gptdoer.parse("Hola, ##! Me llamo ##", ['Fulano', 'Mengano'])
	#term = 'Linux'
	#scope = 'Tecnologia'
	#gptdoer.push_quoted('Responde "Sí" si ## pertenece a ##; de lo contrario, responde "No"', [term, scope])
	#gptdoer.push_quoted('"Sí" si ## pertenece a ##; de lo contrario, "No"', [term, scope])
	#did = gptdoer.do()

	configure(apikey)
	x = 1
	#If('ChatGPT', 'pertenece a ', 'Tecnología').Then(print, 'SI').Else(print, 'No')
	#print(evaluate('Obama fue presidente de Estados Unidos o yo soy Nelson'))
	#print(eval('##+##=##', 2, 2, 9))
	#print(ret('Resume ##', 'Los mejores colores del mundo son aquellos que gustan a todos'))
	#print(ret('Lista de verbos de ##', 'Los mejores colores del mundo son aquellos que gustan a todos'))
	s = '''Los dinosaurios fueron un grupo de reptiles que habitaron la Tierra en la era mesozoica , desde el período triásico superior hasta fines del cretácico (245 a 65 millones de años atrás). Su desaparición marca el límite entre la era mesozoica y la cenozoica, y el comienzo de la denominada edad de los mamíferos. El término dinosaurio proviene del griego (significa "lagarto terrible") y se refiere a ejemplares de lo más diversos: grandes, como el brontosaurio, que pesaba cerca de 75 toneladas, y muy pequeños, como el saltopus, de tan sólo 50 cm de largo.

Los primeros homínidos , por su parte, aparecieron en la Tierra hace relativamente poco, alrededor de 2 millones de años atrás, muchísimo después de que el último de estos grandes reptiles pereciera. Las imágenes de los primeros hombres junto a los dinosaurios no son más que un producto de la fantasía.'''
	print("VERBOS: %s " % verbs(s))
	print("VERBOS EN MODO INFINITIVO: %s " % infinitives(s))
	print("NOMBRES: %s " % nouns(s))
	print("NOMBRES PROPIOS: %s " % proper_nouns(s))
	print("NOMBRES COMUNES: %s " % common_nouns(s))
	print("ADJETIVOS: %s " % adjectives(s))
	print(by_sentence(s, verbs))

