def set_apikey(apikey):
	openai.api_key = apikey

def compare(op1, relation, op2):
	d = 


if __name__ == '__main__':
	gptdoer = Doer('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')
	#pinst = gptdoer.parse("Hola, {}! Me llamo {}", ['Fulano', 'Mengano'])
	term = 'Linux'
	scope = 'Tecnologia'
	#gptdoer.push_quoted('Responde "Sí" si {} pertenece a {}; de lo contrario, responde "No"', [term, scope])
	gptdoer.push_quoted('"Sí" si {} pertenece a {}; de lo contrario, "No"', [term, scope])
	did = gptdoer.do()
	print(did)
