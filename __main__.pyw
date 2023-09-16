from PyQt5.QtWidgets import QApplication
import qdarktheme
import sys
from app.MainWindow import MainWindow

def main():
	app = QApplication(sys.argv)
	qdarktheme.setup_theme()
	geometry = app.desktop().screenGeometry()
	ex = MainWindow(geometry.width(), geometry.height())
	ex.showMaximized()
	sys.exit(app.exec_())
	
if __name__ == '__main__':
	main()