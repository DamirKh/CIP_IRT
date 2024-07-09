import sys
import time, datetime

from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QCheckBox, QHBoxLayout, QDialog

from scanner import Scaner
from ip_addr_widget import IPAddressWidget, SystemNameWidget

from global_data import global_data


class AddSystemDialog(QDialog):
    """Main window with a button to trigger the long task."""

    # Define a signal to emit data
    data_ready = pyqtSignal(str, str, bool)  # Arguments for name, IP, deep scan

    def __init__(self, parent = None):
        # # super().__init__()
        # super().__init__(parent)
        # # super(AddSystemDialog, self).__init__(parent)
        # self.setWindowTitle("Add new entry point")
        #
        # self.system_name = SystemNameWidget()
        #
        # self.ip_widget = IPAddressWidget()
        # self.ip_widget.ip_input.textChanged.connect(self.validate_ip)  # Connect to validate_ip
        #
        # # Create a layout for the checkbox and label
        # checkbox_layout = QHBoxLayout()
        #
        # self.deep_scan_checkbox = QCheckBox('Deep scan')
        # checkbox_layout.addWidget(self.deep_scan_checkbox)
        #
        # self.cn_label = QLabel("Now scanning CN node: [--]")
        # font = QFont("Courier New", 10)  # Choose a monospace font
        # self.cn_label.setFont(font)
        # checkbox_layout.addWidget(self.cn_label)
        #
        # self.label = QTextEdit()
        # self.label.setReadOnly(True)
        # self.button = QPushButton("Start scan")
        # self.button.clicked.connect(self.start_task)
        #
        # layout_name_ip = QHBoxLayout()
        # layout_name_ip.addWidget(self.system_name)
        # layout_name_ip.addWidget(self.ip_widget)
        #
        # layout = QVBoxLayout()
        # # layout.addWidget(self.system_name)
        # # layout.addWidget(self.ip_widget)
        # layout.addLayout(layout_name_ip)
        # layout.addLayout(checkbox_layout)  # Add the checkbox layout
        # # layout.addWidget(self.deep_scan_checkbox)
        # layout.addWidget(self.label)
        # layout.addWidget(self.button)
        # self.setLayout(layout)
        #
        # self.validate_ip()
        super().__init__(parent)
        self.setWindowTitle("Add new entry point")

        # Widgets
        self.system_name = SystemNameWidget()
        self.ip_widget = IPAddressWidget()
        self.ip_widget.ip_input.textChanged.connect(self.validate_ip)
        self.deep_scan_checkbox = QCheckBox('Deep scan')
        self.cn_label = QLabel("Now scanning CN node: [--]")
        self.cn_label.setFont(QFont("Courier New", 10))
        self.label = QTextEdit()
        self.label.setReadOnly(True)
        self.button_scan = QPushButton("Start scan")
        self.button_scan.clicked.connect(self.start_task)
        self.button_cancel = QPushButton("Cancel")
        self.button_cancel.clicked.connect(self.reject)
        self.button_add = QPushButton("Add")
        self.button_add.clicked.connect(self.accept)

        # Layouts
        layout_name_ip = QHBoxLayout()  # Horizontal layout for name and IP
        layout_name_ip.addWidget(self.system_name)
        layout_name_ip.addWidget(self.ip_widget)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.deep_scan_checkbox)
        checkbox_layout.addWidget(self.cn_label)

        button_layout = QHBoxLayout()  # Horizontal layout for buttons
        button_layout.addWidget(self.button_scan)
        button_layout.addWidget(self.button_cancel)
        button_layout.addWidget(self.button_add)

        main_layout = QVBoxLayout()  # Main vertical layout
        main_layout.addLayout(layout_name_ip)
        main_layout.addLayout(checkbox_layout)
        main_layout.addWidget(self.label)
        main_layout.addLayout(button_layout)  # Add button layout

        self.setLayout(main_layout)

        self.validate_ip()  # Initial validation

    def _update_cn_node_current(self, cn_node):
        self.cn_label.setText(f"Now scanning CN node: [{cn_node}]")

    def validate_ip(self):
        """Validate the IP address and enable/disable the button."""
        if self.ip_widget.valid:
            self.button_scan.setEnabled(True)  # Enable button if valid
        else:
            self.button_scan.setEnabled(False)  # Disable button if empty

    def start_task(self):
        """Starts the worker thread and updates the label with progress."""
        self.button_scan.setEnabled(False)

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
        self.button_scan.setEnabled(True)
        # Scroll to the end
        cursor = self.label.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.label.setTextCursor(cursor)
        global_data.store_data()

    def accept(self):
        system_name = self.system_name.get_system_name()  # Get data from widgets
        ip_address = self.ip_widget.get_ip()
        deep_scan = self.deep_scan_checkbox.isChecked()

        # Emit the signal with the data
        self.data_ready.emit(system_name, ip_address, deep_scan)

        # Close the dialog
        super().accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AddSystemDialog()
    window.show()
    sys.exit(app.exec())
