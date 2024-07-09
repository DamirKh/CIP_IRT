import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator

class IPAddressWidget(QWidget):
    def __init__(self):
        super().__init__()

        # self.setWindowTitle("IP Address Input")

        self.ip_label = QLabel("Enter IP Address:")
        self.ip_input = QLineEdit()

        self._valid = False

        # Create the validator from the regular expression
        regex = QRegularExpression(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        )
        self.validator = QRegularExpressionValidator(regex)
        self.ip_input.setValidator(self.validator)

        layout = QVBoxLayout()
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)
        self.setLayout(layout)

        self.ip_input.textChanged.connect(self.validate_ip)
        self.validate_ip()

    def validate_ip(self):
        ip = self.ip_input.text()
        if ip:
            if self.validator.validate(ip, 0)[0] == QRegularExpressionValidator.State.Acceptable:  # Use QRegularExpressionValidator.State
                self.ip_input.setStyleSheet("background-color: lightgreen;")
                self._valid = True
            else:
                self.ip_input.setStyleSheet("background-color: lightcoral;")
                self._valid = False
        else:
            self.ip_input.setStyleSheet("background-color: lightcoral;")
            self._valid = False
            # self.ip_input.setStyleSheet("")

    @property
    def valid(self):
        return self._valid

    def get_ip(self):
        return self.ip_input.text()

class SystemNameWidget(QWidget):
    def __init__(self):
        super().__init__()

        # self.setWindowTitle("IP Address Input")

        self._label = QLabel("System Name:")
        self._input = QLineEdit()

        self._valid = False

        # # Create the validator from the regular expression
        # regex = QRegularExpression(
        #     r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        # )
        # self.validator = QRegularExpressionValidator(regex)
        # self._input.setValidator(self.validator)

        layout = QVBoxLayout()
        layout.addWidget(self._label)
        layout.addWidget(self._input)
        self.setLayout(layout)

        self._input.textChanged.connect(self.validate_input)
        self.validate_input()

    def validate_input(self):
        system_name = self._input.text()
        if system_name:
            if not " " in system_name:
                self._input.setStyleSheet("background-color: lightgreen;")
                self._valid = True
            else:
                self._input.setStyleSheet("background-color: lightcoral;")
                self._valid = False
        else:
            self._input.setStyleSheet("background-color: lightcoral;")
            self._valid = False

    @property
    def valid(self):
        return self._valid

    def get_system_name(self):
        return self._input.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = IPAddressWidget()
    widget.show()

    sys.exit(app.exec())