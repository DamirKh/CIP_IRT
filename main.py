import sys
import time, datetime

from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QCheckBox, QHBoxLayout

from scanner import Scaner
from ip_addr_widget import IPAddressWidget

import global_data


class MainWindow(QWidget):
    """Main window with a button to trigger the long task."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add new entry point")

        self.ip_widget = IPAddressWidget()
        self.ip_widget.ip_input.textChanged.connect(self.validate_ip)  # Connect to validate_ip

        # Create a layout for the checkbox and label
        checkbox_layout = QHBoxLayout()

        self.deep_scan_checkbox = QCheckBox('Deep scan')
        checkbox_layout.addWidget(self.deep_scan_checkbox)

        self.cn_label = QLabel("Now scanning: [--]")
        font = QFont("Courier New", 10)  # Choose a monospace font
        self.cn_label.setFont(font)
        checkbox_layout.addWidget(self.cn_label)

        self.label = QTextEdit()
        self.label.setReadOnly(True)
        self.button = QPushButton("Start scan")
        self.button.clicked.connect(self.start_task)

        layout = QVBoxLayout()
        layout.addWidget(self.ip_widget)
        layout.addLayout(checkbox_layout)  # Add the checkbox layout
        # layout.addWidget(self.deep_scan_checkbox)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.validate_ip()

    def _update_cn_node_current(self, cn_node):
        self.cn_label.setText(f"Now scanning: [{cn_node}]")

    def validate_ip(self):
        """Validate the IP address and enable/disable the button."""
        if self.ip_widget.valid:
            self.button.setEnabled(True)  # Enable button if valid
        else:
            self.button.setEnabled(False)  # Disable button if empty

    def start_task(self):
        """Starts the worker thread and updates the label with progress."""
        self.button.setEnabled(False)

        self.log = []
        self.log.append(f'Task started at {datetime.datetime.now()}')

        self.worker = Scaner(self.ip_widget.get_ip(), self.deep_scan_checkbox.isChecked())
        self.worker.progress.connect(self.update_progress)
        self.worker.cn_node_current.connect(self._update_cn_node_current)
        self.worker.finished.connect(self.task_finished)
        self.worker.communication_error.connect(self.handle_communication_error)
        # try:
        self.worker.start()
        # except CommError


    def handle_communication_error(self, err):
        """Handles the list of discovered ControlNet paths."""
        self.log.append(f'!!! Communication error: {err}')
        self.label.setText('\r'.join(self.log))
        # Now you can use 'paths' to trigger additional scans

    def update_progress(self, value: str):
        """Updates the label with the progress value."""
        if len(value):
            if value.startswith('+'):  # add some to prevision string
                self.log[-1] += value[1:]
            else:
                self.log.append(value)  # add new string
        t = '\r'.join(self.log)
        self.label.setText(t)
        # Scroll to the end
        cursor = self.label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.label.setTextCursor(cursor)

    def task_finished(self):
        """Resets the label and re-enables the button."""
        self.log.append(f"Task Completed at {datetime.datetime.now()}")
        self.label.setText('\r'.join(self.log))
        self.button.setEnabled(True)
        # Scroll to the end
        cursor = self.label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.label.setTextCursor(cursor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
