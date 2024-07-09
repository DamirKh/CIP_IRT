import sys
import time

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal

from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QColor, QBrush

import ping_lib as ping  # Import your ping library

class PingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ping Widget")

        # UI Elements
        self.ip_input = QLineEdit()
        self.ping_button = QPushButton("Ping")
        self.result_label = QLabel()

        # Create 5 square labels
        self.square_labels = []
        for _ in range(5):
            label = QLabel()
            label.setStyleSheet("background-color: gray;")
            label.setFixedSize(QSize(30, 30))
            self.square_labels.append(label)

        # Layouts
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter IP Address:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(self.ping_button)
        layout.addWidget(self.result_label)

        # Create a horizontal layout for the square labels
        square_layout = QHBoxLayout()
        for label in self.square_labels:
            square_layout.addWidget(label)

        layout.addLayout(square_layout)  # Add the square layout to the main layout
        self.setLayout(layout)

        # Connect Signals and Slots
        self.ping_button.clicked.connect(self.start_ping)

        # Initialize ping thread
        self.ping_thread = None
        self.timer = None
        self.ping_results = None
        self.current_ping_index = 0

    def start_ping(self):
        ip_address = self.ip_input.text()
        if not ip_address:
            QMessageBox.warning(self, "Error", "Please enter an IP address.")
            return

        self.ping_button.setEnabled(False)

        # Start pinging
        self.ping_thread = PingThread(ip_address)
        self.ping_thread.finished.connect(self.ping_finished)
        self.ping_thread.progress.connect(self.update_progress)
        self.ping_thread.ping_result.connect(self.update_square_label)
        self.ping_thread.start()

        # Start the timer to update the progress bar
        self.timer = QTimer()
        # self.timer.timeout.connect(self.update_progress)  # Use update_progress for both progress and result label
        self.timer.start(500)

    def update_progress(self, progress_message):
        # Update the result label with progress messages and ping results
        self.result_label.setText(progress_message)

    def update_square_label(self, success):
        # Update the color of the square label based on ping result
        if success:
            self.square_labels[self.current_ping_index].setStyleSheet("background-color: green;")
        else:
            self.square_labels[self.current_ping_index].setStyleSheet("background-color: red;")
        self.current_ping_index = (self.current_ping_index + 1) % len(self.square_labels)

    def ping_finished(self):
        self.timer.stop()
        self.ping_button.setEnabled(True)

        if self.ping_results:
            max_rtt, min_rtt, avg_rtt, packet_loss = self.ping_results
            self.update_progress(  # Pass the message to update_progress
                f"Max RTT: {max_rtt} ms\nMin RTT: {min_rtt} ms\nAvg RTT: {avg_rtt} ms\nPacket Loss: {packet_loss:.2f}%"
            )
        else:
            self.update_progress("Ping completed.")  # Pass the message to update_progress


class PingThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    ping_result = pyqtSignal(bool)  # Signal to indicate ping success

    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.results = None

    def run(self):
        try:
            self.results = ping.quiet_ping(self.ip_address)

            for _ in range(5):
                self.progress.emit(f"Pinging {self.ip_address}...")
                success = bool(self.results[0])  # Assume success if max_rtt is not None
                self.ping_result.emit(success)
                if success:
                    time.sleep(1)  # Adjust the sleep time for the visual effect
                else:
                    time.sleep(0.5)  # Adjust the sleep time for the visual effect

        except Exception as e:
            self.progress.emit(f"Error: {e}")

        finally:
            self.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PingWidget()
    window.show()
    sys.exit(app.exec())