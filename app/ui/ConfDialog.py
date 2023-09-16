import sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ConfDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.values = None

        self.setWindowTitle("Configuración")
        self.layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Create the "Motor de escritura" tab
        self.motor_tab = QWidget()
        self.motor_layout = QFormLayout()
        self.motor_groupbox = QGroupBox("Motor de escritura")
        self.motor_groupbox.setLayout(self.motor_layout)
        self.motor_tab.layout = QVBoxLayout()
        self.motor_tab.layout.addWidget(self.motor_groupbox)
        self.motor_tab.setLayout(self.motor_tab.layout)

        self.gpt_group = QGroupBox("GPT Version")
        self.gpt_params_group = QGroupBox("Configuración")
        self.gpt_layout = QVBoxLayout()

        self.gpt_buttons = QButtonGroup()
        self.gpt_35_button = QRadioButton("GPT 3.5")
        self.gpt_4_button = QRadioButton("GPT-4")
        self.gpt_buttons.addButton(self.gpt_35_button)
        self.gpt_buttons.addButton(self.gpt_4_button)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0, 1)
        self.temperature.setSingleStep(0.05)
        self.temperature
        self.top_p = QDoubleSpinBox()
        self.top_p.setRange(0, 1)
        self.top_p.setSingleStep(0.05)
        self.presencePenalty = QDoubleSpinBox()
        self.presencePenalty.setRange(0, 2)
        self.presencePenalty.setSingleStep(0.05)
        self.frequencyPenalty = QDoubleSpinBox()
        self.frequencyPenalty.setRange(0, 2)
        self.frequencyPenalty.setSingleStep(0.05)
        self.maxTokens = QSpinBox()
        self.maxTokens.setRange(0, 1500)
        self.maxTokens.setSingleStep(5)

        self.gpt_layout.addWidget(self.gpt_35_button)
        self.gpt_layout.addWidget(self.gpt_4_button)
        self.gpt_group.setLayout(self.gpt_layout)
        self.motor_tab.layout.addWidget(self.gpt_params_group)
        

        self.gpt_params_layout = QFormLayout()
        self.gpt_params_layout.addRow(QLabel("TEMPERATURE:"), self.temperature)
        self.gpt_params_layout.addRow(QLabel("TOP P:"), self.top_p)
        self.gpt_params_layout.addRow(QLabel("PRESENCE PENALTY:"), self.presencePenalty)
        self.gpt_params_layout.addRow(QLabel("FREQUENCY PENALTY:"), self.frequencyPenalty)
        self.gpt_params_layout.addRow(QLabel("MAX TOKENS:"), self.maxTokens)
        self.gpt_params_group.setLayout(self.gpt_params_layout)


        self.retries_spinbox = QSpinBox()
        self.retries_spinbox.setRange(1, 1000)
        self.latency_spinbox = QSpinBox()
        self.latency_spinbox.setRange(1, 1000)
        self.errorLatency = QSpinBox()
        self.errorLatency.setRange(1, 1000)
        self.retriesAfterError = QSpinBox()
        self.retriesAfterError.setRange(1, 1000)

        self.motor_layout.addRow(self.gpt_group)
        self.motor_layout.addRow(QLabel("Retries:"), self.retries_spinbox)
        self.motor_layout.addRow(QLabel("Latency:"), self.latency_spinbox)
        self.motor_layout.addRow(QLabel("Error latency:"), self.errorLatency)
        self.motor_layout.addRow(QLabel("Retries after error:"), self.retriesAfterError)

        # Create the "Autoenlazado" tab
        self.autoenlazado_tab = QWidget()
        self.autoenlazado_layout = QFormLayout()
        self.autoenlazado_groupbox = QGroupBox("Autoenlazado")
        self.autoenlazado_groupbox.setLayout(self.autoenlazado_layout)
        self.autoenlazado_tab.layout = QVBoxLayout()
        self.autoenlazado_tab.layout.addWidget(self.autoenlazado_groupbox)
        self.autoenlazado_tab.setLayout(self.autoenlazado_tab.layout)

        self.min_kw_spinbox = QSpinBox()
        self.max_kw_spinbox = QSpinBox()
        self.tld_entry = QLineEdit()
        self.tld_entry.setPlaceholderText('co.in')
        self.num_spinbox = QSpinBox()
        self.stop_spinbox = QSpinBox()
        self.pause_spinbox = QSpinBox()
        self.delay_spinbox = QSpinBox()

        self.autoenlazado_layout.addRow(QLabel("MIN_KW:"), self.min_kw_spinbox)
        self.autoenlazado_layout.addRow(QLabel("MAX_KW:"), self.max_kw_spinbox)
        self.autoenlazado_layout.addRow(QLabel("TLD:"), self.tld_entry)
        self.autoenlazado_layout.addRow(QLabel("NUM:"), self.num_spinbox)
        self.autoenlazado_layout.addRow(QLabel("STOP:"), self.stop_spinbox)
        self.autoenlazado_layout.addRow(QLabel("PAUSE:"), self.pause_spinbox)
        self.autoenlazado_layout.addRow(QLabel("DELAY:"), self.delay_spinbox)

        # Add tabs to the tab widget
        self.tab_widget.addTab(self.motor_tab, "Motor de escritura")
        self.tab_widget.addTab(self.autoenlazado_tab, "Autoenlazado")

        # Save button
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_values)

        # Add tab widget and save button to the main layout
        self.layout.addWidget(self.tab_widget)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

        self.load_values()


    def save_values(self):
        values = {
            "engine": "gpt-3.5-turbo" if self.gpt_35_button.isChecked() else "gpt-4",
            'retries_after_error': self.retriesAfterError.value(),
            'error_latency': self.errorLatency.value(),
            'temperature' : self.temperature.value(),
            'top_p' : self.top_p.value(),
            'frequency_penalty' : self.frequencyPenalty.value(),
            'presence_penalty' : self.presencePenalty.value(),
            'max_tokens' : self.maxTokens.value(),
            "retries": self.retries_spinbox.value(),
            "latency": self.latency_spinbox.value(),
            "min_kw": self.min_kw_spinbox.value(),
            "max_kw": self.max_kw_spinbox.value(),
            "tld": self.tld_entry.text() if len(self.tld_entry.text().strip()) else 'co.in',
            "num": self.num_spinbox.value(),
            "stop": self.stop_spinbox.value(),
            "pause": self.pause_spinbox.value(),
            "min_kw": self.min_kw_spinbox.value(),
            "delay": self.delay_spinbox.value()
        }

        with open("atwood.conf", "w") as file:
            json.dump(values, file, indent=4)

        self.hide()

    def load_values(self):
        try:
            with open("atwood.conf", "r") as file:
                values = json.load(file)

            self.values = values

            # Set GPT version
            if values.get("engine") == "gpt-3.5-turbo":
                self.gpt_35_button.setChecked(True)
            elif values.get("engine") == "gpt-4":
                self.gpt_4_button.setChecked(True)
            else:
                self.gpt_35_button.setChecked(True)

            # Set Motor de escritura tab values
            self.retries_spinbox.setValue(values.get("retries", 0))
            self.latency_spinbox.setValue(values.get("latency", 0))
            self.errorLatency.setValue(values.get('error_latency', 0))
            self.retriesAfterError.setValue(values.get('retries_after_error', 0))
            self.temperature.setValue(values.get('temperature', 0))
            self.top_p.setValue(values.get('top_p', 0))
            self.presencePenalty.setValue(values.get('presence_penalty', 0))
            self.frequencyPenalty.setValue(values.get('frequency_penalty', 0))
            self.maxTokens.setValue(values.get('max_tokens', 0))

            # Set Autoenlazado tab values
            self.min_kw_spinbox.setValue(values.get("min_kw", 0))
            self.max_kw_spinbox.setValue(values.get("max_kw", 0))
            self.tld_entry.setText(values.get("tld", ''))
            self.num_spinbox.setValue(values.get("num", 0))
            self.stop_spinbox.setValue(values.get("stop", 0))
            self.pause_spinbox.setValue(values.get("pause", 0))
            self.min_kw_spinbox.setValue(values.get("min_kw", 0))
            self.delay_spinbox.setValue(values.get("delay", 0))
        except FileNotFoundError:
            print("No se encuentra el archivo de configuración")
        except json.JSONDecodeError:
            print("Formato JSON inválido en el archivo de configuración.")

    def getValues(self):
        return self.values


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ConfDialog()
    dialog.show()
    sys.exit(app.exec_())
