import re
import os
import sys
import time
from colorama import Fore

#################################################################################################
	### AUXILIAR METHODS ###
#################################################################################################

def printerr(head, body):
	print(Fore.RED + head + ": " + Fore.YELLOW + body + Fore.RESET)

def printwarn(head, body):
	print(Fore.YELLOW + head + ": " + Fore.YELLOW + body + Fore.RESET)

def log(message):
	#print(message)
	with open('log', 'a') as file:
		file.write('%s: %s\n\n' % ( time.strftime("%Y-%m-%d at %H:%M:%S", time.localtime()), message) )

def get_platform():
	platforms = {
	'linux1' : 'Linux',
	'linux2' : 'Linux',
	'darwin' : 'OS X',
	'win32' : 'Windows'
	}

	if sys.platform not in platforms:
		return sys.platform

	return platforms[sys.platform]

def mkDirIfNotExists(directory_path):
	if not os.path.exists(directory_path):
		os.makedirs(directory_path)

def toValidFileName(filename):
	filename = filenameNoExt(filename)
	filename = re.sub(r'[^\w\s-]', '', filename).strip()

	return filename

def basenameNoExt(path):
	return os.path.splitext(os.path.basename(path))[0]

def filenameNoExt(filename):
	return os.path.splitext(filename)[0]

def removeLastDot(text):

	while text.endswith('.'): 
		text = text[:-1] 

	return text

#******************************************************************************************************
#OBTENER TEXTO ENLAZABLE, ES DECIR TODO EL CONTENIDO EXCLUYENDO HEADINGS Y METADESCRIPCION
#******************************************************************************************************

def getLinkeableText(article):

	ltext = ''
	
	for e in article:
		s = e['content'].strip()
		if s.find('id="meta"') == -1:
			if len(s):
				ltext = ltext + s + '\n'

	return ltext

#******************************************************************************************************
#ELIMINAR ETIQUETAS HTML DEL CONTENIDO
#******************************************************************************************************

def remove_html_tags(text):
	clean = re.compile('<.*?>')
	return re.sub(clean, '', text)

#******************************************************************************************************
#PARA LOS TEXTOS HTML CON ETIQUETAS DE CIERRE FALTANTES
#******************************************************************************************************

def insert_missing_close_tags(html):
    stack = []
    pattern = re.compile(r'<(/)?(\w+)(\s|>)?')

    for match in pattern.finditer(html):
        tagname = match.group(2).lower()
        if not match.group(1) or not match.group(1) == "/":
            stack.append(tagname)
        else:
            while stack and not stack[-1] == tagname:
                html += f"</{stack.pop()}>"
            if stack:
                stack.pop()
    
    while stack:
        html += f"</{stack.pop()}>"

    return html

#******************************************************************************************************
#ELIMINA LOS ESPACIOS SOBRANTES DEL TEXTO
#******************************************************************************************************

def remove_extra_spaces(text):
	lines = text.splitlines()
	fixed_text = ''

	for line in lines:
		if len(line.strip()):
			words = line.strip().split()
			fixed_line = ' '.join(words)
			fixed_line.strip()
			fixed_text = fixed_text + fixed_line + '\n'
	
	return fixed_text

#******************************************************************************************************
#UNE LAS LINEAS PARTIDAS EN EL MARKDOWN TEXT
#******************************************************************************************************

def fix_markdown_line_breaks(markdown_text):
	fixed = markdown_text.replace('\n\n', '!~!~') #salvaguarda los saltos de linea dobles
	fixed = fixed.replace('\n', ' ') #elimina los saltos de linea
	fixed = remove_extra_spaces(fixed) #elimina los espacios sobrantes
	fixed = fixed.replace('!~!~', '\n\n') #recupera los saltos de linea dobles
	
	clean = ''
	lines = fixed.split('\n\n')
	
	for line in lines:
		clean = clean + line.strip() + '\n\n'
	     
	fixed = clean
	return fixed


#******************************************************************************************************
#
#******************************************************************************************************

def is_list_item(line):
    # Regular expressions to match different list item formats
    patterns = [
        r'^\s*-\s',         # - Example
		r'^[-+]?\b\d+(?:[.,]\d+)?(?=[.\-)\s]|$)',
		r'^\s*[a-zA-Z]\)\s',   # a) Example
		r'^\s*\([a-zA-Z]+\)\s', # (a) Example
		r'^\s*[a-zA-Z]\.\s',   # a. Example
    ]
    
    for pattern in patterns:
        if re.match(pattern, line):
            return True
    
    return False


def isBlockedList(block):
	return is_list_item(block)

def getBlockedListPattern(block):
	patterns = [
	r'^\s*-\s',        # - Example
	r'^[-+]?\b\d+(?:[.,]\d+)?(?=[.\-)\s]|$)',
	r'^\s*[a-zA-Z]\)\s',   # a) Example
	r'^\s*\([a-zA-Z]+\)\s', # (a) Example
	r'^\s*[a-zA-Z]\.\s',   # a. Example
	]

	for pattern in patterns:
		if re.match(pattern, block):
			result = pattern.replace('^', '')
			return result, re.findall(result, block)

#******************************************************************************************************
#
#******************************************************************************************************

def convertHeading(line):


		if '[h2]:' in line:
			h = line.replace('#', '').replace('**', '').replace('[h2]:', '').strip()
			return f'## {h}'
		elif '[h1]:' in line:
			h = line.replace('#', '').replace('**', '').replace('[h1]:', '').strip()
			return f'# {h}'
		elif isBlockedList(line):
			line = line.replace('\n', ' ').replace(' ', ' ')
			listStr = ''
			pattern, bullets = getBlockedListPattern(line)
			list_items = re.split(pattern, line)
			
			for i in range(len(list_items)):
				if len(list_items[i].strip()):
					if i <= len(bullets):
						bullet = bullets[i-1]
					else:
						bullet = ''
					listStr = listStr + bullet + list_items[i].strip() + '\n\n'
	
			return listStr

		return line

#******************************************************************************************************
#
#******************************************************************************************************


#******************************************************************************************************
#
#******************************************************************************************************

if __name__ == '__main__':

	markdown_text = """
No obstante, hay muchas cosas que puedes hacer para mejorar la UX sin
sacrificar el SEO. Algunas ideas son: 

1) **Sitio rápido:** asegúrate de que las páginas carguen rápidamente tanto en
  desktop como mobile. 
2) **Navegación simple:** usa una estructura clara y coherente para guiar a tus
  usuarios a través del contenido relevante.
3)    **Buena legibilidad:** utiliza tipografías amigables con el lector y tamaños
  adecuados para facilitar la lectura.
4) **Multimedia útil:** agrega imágenes, videos o infografías relevantes que
  complementen tu información. 

Todas estas acciones no solo mejoran la UX, sino que también incrementan la
retención de usuarios y el tiempo en sitio. Y estas son métricas muy valiosas
para los motores de búsqueda. 
	"""

	fmarkdown = fix_markdown_line_breaks(markdown_text)
	#print(fmarkdown)
	lines = fmarkdown.split("\n\n")
	result = ''

	for line in lines:
		#print(f"LINE: {line}")
		cmarkdown = convertHeading(line)
		result = result + cmarkdown + '\n\n'
	print(f'{Fore.GREEN}MARKDOWN TRANSFORMED:{Fore.WHITE}\n{result}')


