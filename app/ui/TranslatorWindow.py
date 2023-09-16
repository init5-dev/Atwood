import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.origin_text_edit = QTextEdit(self)
        self.origin_text_edit.setPlaceholderText("Enter origin text here")
        self.origin_text_edit.setGeometry(20, 40, 400, 300)

        self.translated_text_edit = QTextEdit(self)
        self.translated_text_edit.setPlaceholderText("Translated text will appear here")
        self.translated_text_edit.setGeometry(440, 40, 400, 300)

        self.language_listbox = QListWidget(self)
        self.language_listbox.addItem("English")
        self.language_listbox.addItem("Spanish")
        self.language_listbox.setGeometry(20, 360, 400, 100)

        open_button = QPushButton("Open File", self)
        open_button.clicked.connect(self.open_file_dialog)
        open_button.setGeometry(20, 480, 80, 30)

        save_button = QPushButton("Save File", self)
        save_button.clicked.connect(self.save_file_dialog)
        save_button.setGeometry(120, 480, 80, 30)

        start_trans_button = QPushButton("Start Translation", self)
        start_trans_button.clicked.connect(self.start_translation)
        start_trans_button.setGeometry(220 ,480 ,120 ,30)

        cancel_trans_button = QPushButton("Cancel Translation",self)
        cancel_trans_button.clicked.connect(self.cancel_translation) 
        cancel_trans_button.setGeometry (350 ,480 ,120 ,30)

        self.setGeometry(100, 100, 880, 540)
        self.setWindowTitle("Document Translator")

    def open_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Documents (*.docx *.odt *.pdf *.html *.txt)", options=options)

        if file_name:
            try:
                extension = file_name.split('.')[-1]

                if extension == 'docx':
                    document = Document(file_name)
                    content = '\n'.join([paragraph.text for paragraph in document.paragraphs])
                elif extension == 'odt':
                    odt_document = odt_text.load(file_name).getroot()
                    content = '\n'.join([text_element.data for text_element in odt_document.findall('.//{http://www.w3.org/1999/XSL/Transform}#text')])
                else:
                    with open(file_name, 'r') as file:
                        content = file.read()

                self.origin_text_edit.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def save_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Documents (*.docx *.odt *.pdf *.html *.txt)", options=options)

        if file_path:
            try:
                extension = file_path.split('.')[-1]
                translated_text=self.translated_text_edit.toPlainText()

                if extension == 'docx':
                    document_translated= Document()
                    document_translated.add_paragraph(translated_text)
                    document_translated.save(file_path)
                elif extension == 'odt':
                    odt_document_translated = odt_text.ODFDocument()
                    text_paragraph = odt_text.P(text=translated_text)
                    odt_document_translated.body.append(text_paragraph)
                    odt_document_translated.save(file_path)
                else:
                    with open(file_path, 'w') as file:
                        file.write(translated_text)

                QMessageBox.information(self, "Success", "File saved successfully.")

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def start_translation(self):
        origin_text = self.origin_text_edit.toPlainText()
        language = self.language_listbox.currentItem().text()

        # Add your translation code here
        # Example: translated_text = translate(origin_text, language)

        translated_text = f"Translated text ({language}): {origin_text}"
        self.translated_text_edit.setPlainText(translated_text)

    def cancel_translation(self):
        self.origin_text_edit.clear()
        self.translated_text_edit.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    translator_window = TranslatorWindow()
    translator_window.show()
    sys.exit(app.exec())
