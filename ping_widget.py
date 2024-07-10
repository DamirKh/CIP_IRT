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
# from PyQt6.QtGui import QColor, QBrush

# import python_ping3
from host_ping import ping


class PingWidget(QWidget):
    def __init__(self, q=10, size=20):
        super().__init__()
        self._ip_address = '127.0.0.1'

        # Create q square labels
        self._results = []
        self.square_labels = []
        for _ in range(q):
            label = QLabel()
            label.setStyleSheet("background-color: gray;")
            label.setFixedSize(QSize(size, size))
            self.square_labels.append(label)
            self._results.append(None)

        # Create a horizontal layout for the square labels
        square_layout = QHBoxLayout()
        # Add a spacer first
        spacer_hor = QWidget()
        square_layout.addWidget(spacer_hor, stretch=1)
        for label in self.square_labels:
            square_layout.addWidget(label)
        self.setLayout(square_layout)

        # Initialize ping thread
        self.ping_thread = None
        self.timer = None
        self.ping_results = None
        self.current_ping_index = 0

        # self.start_ping()

    def start_ping(self, ip_address: str):
        self._ip_address = ip_address
        self._results = [None] * len(self.square_labels)

        # Start pinging
        self.ping_thread = PingThread(self._ip_address)
        self.ping_thread.ping_result.connect(self.update_square_label)
        self.ping_thread.start()

        # Start the timer to update the progress bar
        self.timer = QTimer()
        # self.timer.timeout.connect(self.update_progress)  # Use update_progress for both progress and result label
        self.timer.start(500)

    def stop_ping(self):
        if self.ping_thread:
            self.ping_thread.stop()
            self.ping_thread.wait()  # Wait for the thread to finish
            self.ping_thread = None

        self.timer.stop()

    def update_square_label(self, success):
        # Update the color of the square label based on ping result
        # print(self._results)
        self._results.pop(0)
        self._results.append(success)
        for i, result in enumerate(self._results):
            if result is True:
                self.square_labels[i].setStyleSheet("background-color: green;")
            if result is False:
                self.square_labels[i].setStyleSheet("background-color: red;")
            if result is None:
                self.square_labels[i].setStyleSheet("background-color: gray;")


class PingThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    ping_result = pyqtSignal(bool)  # Signal to indicate ping success
    stopped = pyqtSignal()

    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.results = None
        self._running = True

    def run(self):
        try:
            while self._running:  # Endless ping loop
                # Use ping_lib to ping the IP address
                ping_result = ping(self.ip_address, packages=4, wait=2)
                success = bool(ping_result == 0)  # True if ping is successful

                self.progress.emit(f"Pinging {self.ip_address}...")
                self.ping_result.emit(success)
                if success:
                    time.sleep(1)  # Adjust the sleep time for the visual effect
                else:
                    time.sleep(1)  # Adjust the sleep time for the visual effect

        except Exception as e:
            self.progress.emit(f"Error: {e}")

        finally:
            self.finished.emit()

    def stop(self):
        """Stops the ping thread."""
        self._running = False
        self.stopped.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PingWidget()
    window.start_ping('ya.ru')
    window.show()
    sys.exit(app.exec())
