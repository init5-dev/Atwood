import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer

class RetryDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('¿Reintentar?')

        # Set up the UI elements for the dialog
        self.messageLabel = QLabel("Ocurrió un error durante la escritura. ¿Deseas reintentarla?")
        self.btn_yes = QPushButton("Sí")
        self.btn_no = QPushButton("No")
        self.countdownLabel = QLabel()

        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)
        
        # Add UI elements to layout and set it as main layout
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        
        hbox.addWidget(self.btn_yes)
        hbox.addWidget(self.btn_no)
        vbox.addWidget(self.messageLabel)
        vbox.addWidget(self.countdownLabel)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def showEvent(self, event):
       super().showEvent(event)

       # Start a countdown timer when the dialog is first shown
       self.countdown_timer = QTimer()
       self.countdown_timer.setInterval(1000)  # 1 second interval

       # Define function to update message with regressive count
       remaining_time = 10  # Seconds until close dialog (modify as desired)
       def update_message():
           nonlocal remaining_time

           if remaining_time == 0:
               self.accept() # Close dialog when count reaches zero.
               return

           remaining_time -= 1
           self.countdownLabel.setText(f"La escritura se retomará automáticamente en {remaining_time} s")

       # Start countdown timer and connect it to message update function.
       self.countdown_timer.timeout.connect(update_message)
       
       update_message()   # First call before starting timer.
       
       self.countdown_timer.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    dlg_retry = RetryDialog()
    response = dlg_retry.exec_() 
    print(response)
    if response == QDialog.Accepted:
        print("User clicked 'Yes'")
    else:
        print("User clicked 'No'")

    sys.exit(app.exec_())