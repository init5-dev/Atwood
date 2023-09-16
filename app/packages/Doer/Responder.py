import openai
import time

class Responder:

	def __init__(self, apikey):
		self.apikey = apikey
		openai.api_key = self.apikey
		self.retries = 6
		self.retryNumber = 0

	def __get_response(self, prompt, model='gpt-3.5-turbo'):
		
		max_tokens = len(prompt.split(' '))

		return openai.ChatCompletion.create(
				model = model,
				messages = [
							{'role':'system', 'content':'Responde de la manera más concisa posible.'}, 
							{'role':'user', 'content' : prompt}
						   ],
				temperature = 0,
				top_p = 0,
				presence_penalty = 0,
				frequency_penalty = 0,
				max_tokens = max_tokens			
				)

	def responde(self, prompt, model='gpt-3.5-turbo'):
		#print(prompt)
		answer = ''

		try:
			response = self.__get_response(prompt, model)	
		except openai.error.APIConnectionError as e:
			self.retryNumber += 1
			if self.retryNumber <= self.retries:
				print('No se pudo conectar con OpenAI. Intentado en %s segundos...' % self.errorWaiting)
				time.sleep(self.errorWaiting)
				answer = self.responde(prompt, model=model)
				if answer:
					return answer.strip()

				return ''
			else:
				print('Intentos de conectar con OpenAI fallidos.')
				self.retryNumber = 0
				raise e 
                
		answer = answer + response['choices'][0]['message']['content']
		if answer:
			return answer.strip()

		return ''