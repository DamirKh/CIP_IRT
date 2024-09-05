import sys
import time, datetime

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout, QDialog, QTableWidget, QVBoxLayout, QTableWidgetItem, QHeaderView, QFileDialog
)


class LogViewer(QDialog):
    def __init__(self, parent=None, title="Log Viewer"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 400)

        # Create a table widget to display logs
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Time (s)", "Message"])

        # Hide vertical header
        self.table_widget.verticalHeader().setVisible(False)

        # Make message column expandable
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Create a vertical layout for the table
        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)

        # Add export button
        self.export_button = QPushButton("Export to Text File")
        self.export_button.clicked.connect(self.export_logs)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def update_table(self, time_list, log_list):
        self.table_widget.setRowCount(len(log_list))
        for i, (t, msg) in enumerate(zip(time_list, log_list)):
            self.table_widget.setItem(i, 0, QTableWidgetItem(f"{t:.2f}"))
            self.table_widget.setItem(i, 1, QTableWidgetItem(msg))

    def export_logs(self):
        # options = QFileDialog.options()
        # options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Text Files (*.txt)")
        if file_name:
            with open(file_name, 'w') as f:
                for i in range(self.table_widget.rowCount()):
                    time_item = self.table_widget.item(i, 0)
                    msg_item = self.table_widget.item(i, 1)
                    f.write(f"{time_item.text()}\t{msg_item.text()}\n")


class LogWidget(QWidget):
    def __init__(self, log=None, init_label: str = 'Log', viewer_title = "Log Viewer"):
        """
        Log under the button
        :param log:
            (time, message),
            (time, message)...
        :param init_label:
        """
        super().__init__()
        self.viewer_title = viewer_title
        self._start_time = time.time()
        self._log = []
        self._time = []
        if log is None:
            log = []
        else:
            for l in log:
                self._time.append(l[0])
                self._log.append(l[1])

        self.button = QPushButton(init_label)
        self.button.clicked.connect(self.show_log_viewer)

        # Create a horizontal layout for the square labels
        layout = QHBoxLayout()
        layout.addWidget(self.button, stretch=1)
        self.setLayout(layout)

    def start_log(self):
        self._start_time = time.time()
        # Convert start_time to a datetime object
        start_datetime = datetime.datetime.fromtimestamp(self._start_time)
        # Format the datetime object into a human-readable string
        formatted_start_time = start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"Log started at {formatted_start_time}")

    def stop_log(self):
        stop_time = time.time()
        stop_datatime = datetime.datetime.fromtimestamp(stop_time)
        formatted_stop_time = stop_datatime.strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"Log stopped at {formatted_stop_time}")
        self.log(f"Total time = {stop_time - self._start_time}")

    def log(self, message: str = ''):
        self._log.append(message)
        self._time.append(time.time() - self._start_time)
        self.button.setText(message[:20])  # Update button label

    def show_log_viewer(self):
        viewer = LogViewer(self, title=self.viewer_title)
        viewer.update_table(self._time, self._log)
        viewer.exec()


if __name__ == "__main__":
    from PyQt6.QtWidgets import (
        QApplication)

    app = QApplication(sys.argv)
    window = LogWidget()
    window.show()

    window.start_log()
    window.log("Hello!")
    time.sleep(2)
    window.log("Bye!")
    window.stop_log()
    window.show()
    sys.exit(app.exec())
