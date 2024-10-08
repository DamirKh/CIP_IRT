import sys
import time
import platform


from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import QThread, pyqtSignal, QProcess

from PyQt6.QtCore import QTimer, QSize
from host_ping import ping

from serial_generator import StyleSheetGenerator

class PingWidget(QWidget):
    def __init__(self, q=10, size=20):
        super().__init__()
        self._ip_address = '127.0.0.1'

        self.rolling_color = StyleSheetGenerator()

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
        square_layout.addSpacing(size)
        for label in self.square_labels:
            square_layout.addWidget(label)
        square_layout.addSpacing(size)

        self.setLayout(square_layout)

        # Initialize ping thread
        # self.ping_thread = None
        self.timer = None
        self.ping_results = None
        self.current_ping_index = 0
        self._results = [None] * len(self.square_labels)

        self.ping_proc = QProcess()
        self.ping_proc.setProgram('ping')

    def start_ping(self, ip_address: str):
        self._ip_address = ip_address
        system = platform.system()

        # Windows
        if system == "Windows":
            arguments = ['-n', '1', '-w', '1', self._ip_address]
        # Linux/macOS
        else:
            arguments = ['-c', '1', '-w', '1', self._ip_address]

        self.ping_proc.setArguments(arguments)
        self.ping_proc.finished.connect(self.ping_finished)
        # self.ping_proc.start()

        # Start the timer to update the progress bar
        self.timer = QTimer()
        # self.timer.
        self.timer.timeout.connect(self.ping_proc.start)
        self.timer.start(3000)

    def ping_finished(self):
        # pass
        # print(".", end='')
        success = bool(self.ping_proc.exitCode() == 0)  # True if ping is successful
        self.update_square_label(success)


    def stop_ping(self):
        self.ping_proc.kill()
        if self.timer is None:
            pass
        else:
            self.timer.stop()
        self._results = [None] * len(self.square_labels)
        self.update_square_label(None)

    def update_square_label(self, success):
        # Update the color of the square label based on ping result
        # print(self._results)
        self._results.pop(0)
        self._results.append(success)
        for i, result in enumerate(self._results):
            if result is True:
                self.square_labels[i].setStyleSheet("background-color: green;")  # background: rgba(100, 100, 100, 150);
            if result is False:
                self.square_labels[i].setStyleSheet("background-color: red;")
            if result is None:
                self.square_labels[i].setStyleSheet("background-color: gray;")

    def progress_forward(self, *arg):
        for i in range(len(self.square_labels)):
            self.square_labels[i].setStyleSheet(f"background-color: rgba(100, 100, {str(self.rolling_color)}, 255);")  # background: rgba(100, 100, 100, 150);


class PingThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    ping_result = pyqtSignal(bool)  # Signal to indicate ping success
    stopped = pyqtSignal()

    def __init__(self, ip_address):
        super().__init__()
        self.ip_address = ip_address
        self.results = None
        self._running = False

    def run(self):
        self._running = True
        try:
            while self._running:  # Endless ping loop
                # Use ping_lib to ping the IP address
                ping_result = ping(self.ip_address, packages=1, wait=1)
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
