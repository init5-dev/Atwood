from atwriter import AtWriter

def getTitle(text):
	start = text.lower().find('<h1>') + len('<h1>')
	end = text.find('</h1>')
	if start > -1 and end > start:
		return text[start:end]
	else:
		raise Exception('No se encuentra el titulo.')
		return

def fixFileTitle(filename):
	if not len(filename):
		return filename
	badChars = '#%&{}\\<>*¿?/$¡!\'":@+`|='
	possibleEnds = [filename.find('.'), filename.find('?'), filename.find('!')]
	possibleEnds.sort()
	firstEnd = -1
	for end in possibleEnds:
		if end > -1:
			firstEnd = end
			break
	print(possibleEnds)
	print(firstEnd)
	filename = filename[0:firstEnd+1]
	for bc in badChars:
		filename = filename.replace(bc, '')
	return filename

import tkinter as tk
from tkinter import Tk, Button, Entry, Text
from tk_html_widgets import HTMLScrolledText
import re

class HTMLTextHelper:
	def __init__(self, htmlTextWidget):
		self.htmlTextWidget = htmlTextWidget
		self.htmlTextWidget.bind('<KeyPress>', self.on_press)

	def _remove_html_tags(self, text):
		TAG_RE = re.compile(r'<[^>]+>')
		return TAG_RE.sub('', text)

	def _get_html_insert_pos(self, p):
		text = self.htmlTextWidget.get('1.0', tk.END)
		prev2p = text[0:p] #todo el contenido antes del cursor
		next2p = text[p:] #todo el contenido despues del cursor
		htmlEnd = len(self.htmlTextWidget.htmlCode)
		print("END: {}".format(htmlEnd))
		print(prev2p)

		for i in range(htmlEnd):
			prev2_html_p = self._remove_html_tags(self.htmlTextWidget.htmlCode[0: i])
			next2_html_p = self._remove_html_tags(self.htmlTextWidget.htmlCode[i: ])
			print(prev2_html_p + "|" + next2_html_p)
			if prev2p == prev2_html_p and next2p == next2_html_p:
				return i
		return -1

	def insert(self, p, text):
		html_p = self._get_html_insert_pos(p)
		prev = self.htmlTextWidget.htmlCode[0: html_p]
		next = self.htmlTextWidget.htmlCode[html_p:]
		self.htmlTextWidget.set_html(prev + text + next)

	def append(self, text):
		pass

	def remove(self, text):
		pass

	def on_press(self, event):
		prevp = self.htmlTextWidget.get('1.0', tk.INSERT)
		p = len(prevp)
		print(p)
		#self.insert(p, event.char)

class HTMLScrollableText(HTMLScrolledText):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		#self.bind('<KeyPress>', self.key_press)
		self.vbar.pack_forget()
		self.htmlCode = ''
		print('HELL')

	'''def _w_init(self, kwargs):
		super(HTMLScrollableText, self)._w_init(kwargs)
		#self.bind('<KeyRelease>', self.on_release)
		super().bind('<KeyRelease>', lambda e: 'break')
		self.vbar.pack_forget()
		self.htmlCode = ''
		print('HEAVEN')'''


	def fit_height(self):
		super().fit_height()
		self.vbar.pack_forget()

	def set_html(self, html, strip=True):
		super().set_html(html, strip)
		self.htmlCode = html

	def get_html(self, start=0, end=tk.END):
		endPos = -2
		if end == tk.END or end == 'end':
			return self.htmlCode[start:]
		return self.htmlCode[start: end]

	'''def insert(self, p, text, tags=None):
		super().insert(p, text, tags)
		chars = self.get('1.0', p)
		pInsert = len(chars)'''

	'''def key_press(self, event):
		pass'''

class HtmlTestApp(Tk):
	def __init__(self, *args, html=None, **kwargs):
		super().__init__()	
		self.htmlText = HTMLScrollableText(height=15)
		text = \
'''<h1>Que es HTMLScrollableText</h1>
<p>Descubre ahora mismo este maravilloso componente creado por Nelson Ochagavia</p>
<h2>Esto es un <i>ejemplo del widget</i></h2>
<p>Si te gusta, <b>dame like!</b></p>
'''
		self.entry = Text(height = 5)
		self.sendButton = Button(text='Enviar', command=self.send)
		self.htmlText.pack()
		#self.htmlText.bind('<KeyRelease>', self.key_release)
		#self.htmlText.bind('<ButtonRelease>', self.getTextCursor)
		#self.htmlText.bind('<KeyPress>', self.updateCodeView)
		self.helper = HTMLTextHelper(self.htmlText)
		self.htmlCodeView = Text(height = 15)

		self.entry.pack(fill=tk.X)
		self.entry.insert(tk.INSERT, text)
		self.sendButton.pack()
		self.htmlCodeView.pack()

		self.k = None

	def getTextCursor(self, event):
		prevp = self.htmlText.get('1.0', tk.INSERT)
		p = len(prevp)
		print(prevp)

	def send(self):
		HTMLTextHelper(self.htmlText).insert(0, self.entry.get('1.0', tk.END))
		self.htmlCodeView.delete('1.0', tk.END)
		self.htmlCodeView.insert(tk.INSERT, self.htmlText.get_html())

	def key_release(self, event):
		self.htmlText.delete('insert-1c')

	def updateCodeView(self, event):
		#HTMLTextHelper(self.htmlText).insert(p, event.char)
		self.htmlCodeView.delete('1.0', tk.END)
		#print('UPDATING...')
		#print(self.htmlText.get('1.0', tk.END))
		#print(self.htmlText.htmlCode)
		self.htmlCodeView.delete('1.0', tk.END)
		self.htmlCodeView.insert(tk.INSERT, self.htmlText.get_html())


if __name__=="__main__":
	atw = AtWriter('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')
	scope = 'Vender una casa en Chile.'
	author = 'Inversur.'
	reader = 'Publico chileno.'
	style = 'Profesional, natural.'
	extraInstructions = 'Tutea al lector.'
	index = ['Estado del mercado inmobiliario en Chile', 'Requisitos para vender una casa', 'Importancia de contratar un agente inmobiliario', 'Algunos consejos adicionales', 'Conclusiones']
	article = atw.secure_execution(atw.standardArticle(scope, author, reader, style, extraInstructions, index))
	article_len = len(article.split())
	print(article)
	atw.saveLog()
	print("WORDS: {0}\nPROMPT TOKENS: {1}\nCOMPLETION TOKENS: {2}\nTOTAL TOKENS: {3}\nPRICE: {4:.5f}".format(article_len, atw.prompt_tokens, atw.completion_tokens, atw.total_tokens, atw.price))
