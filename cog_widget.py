import sys
import time, datetime

from PyQt6.QtCore import QThread, pyqtSignal, QThreadPool
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout, QDialog, QTableWidget, QVBoxLayout, QTableWidgetItem, QHeaderView, QFileDialog
)

class CheckUsedCogsThread(QThread):
    progress = pyqtSignal(int)

    def __init__(self, pool: QThreadPool):
        super().__init__()
        self.pool = pool
        self._running = False

    def run(self):
        self._running = True
        while self._running:  # Endless check loop
            count = self.pool.activeThreadCount()
            self.progress.emit(count)
            time.sleep(0.5)  # Adjust the sleep time for the visual effect

    def stop(self):
        """Stops the ping thread."""
        self._running = False

class CogWidget(QWidget):
    def __init__(self, pool: QThreadPool):
        """
        """
        super().__init__()
        self._checking_tread = CheckUsedCogsThread(pool)
        self._checking_tread.progress.connect(self.update_cog_counter)

        self.label_cog = QLabel('Cog')
        self.label_cog_counter = QLabel('0')

        # Create a horizontal layout for the square labels
        layout = QHBoxLayout()
        layout.addWidget(self.label_cog_counter)
        layout.addWidget(self.label_cog)
        self.setLayout(layout)
        self._checking_tread.start()

    def update_cog_counter(self, used_cogs: int):
        print(f"Used cogs: {used_cogs}")
        self.label_cog_counter.setText(f"{used_cogs}")



if __name__ == "__main__":
    from PyQt6.QtWidgets import (
        QApplication)

    app = QApplication(sys.argv)
    window = CogWidget()
    window.show()

    window.start_log()
    window.log("Hello!")
    time.sleep(2)
    window.log("Bye!")
    window.stop_log()
    window.show()
    sys.exit(app.exec())
