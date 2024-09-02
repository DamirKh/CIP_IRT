import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QVBoxLayout,
    QCheckBox,
    QMessageBox, QTableWidgetItem,
)
import csv
import pickle
from datetime import datetime

from saver import get_user_data_path

class CSVViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Viewer")

        self.table = QTableWidget()
        self.button_import = QPushButton("Import CSV")
        self.button_import.clicked.connect(self.import_csv)

        self.button_save = QPushButton("Save")
        self.button_save.clicked.connect(self.save_config)

        self.checkboxes = []  # To store checkboxes for each row
        self.system_name = []
        self.entry_point = []
        self.last_scan_time = []

        # self.program_settings_file_path = "settings.pkl"  # Define your settings file path
        self.program_settings_file_path = get_user_data_path() / f"main_prog.cfg"

        layout = QVBoxLayout()
        layout.addWidget(self.button_import)
        layout.addWidget(self.button_save)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def import_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.load_csv(file_path)

    def load_csv(self, file_path):
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.checkboxes = []
        self.system_name = []
        self.entry_point = []
        self.last_scan_time = []

        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            header = next(reader)
            header = ['', *header]

            self.table.setColumnCount(len(header)+1)
            self.table.setHorizontalHeaderLabels(header)

            for row_index, row in enumerate(reader):
                row_count = self.table.rowCount()
                self.table.insertRow(row_count)

                checkbox = QCheckBox()
                checkbox.setChecked(True)
                self.checkboxes.append(checkbox)
                self.table.setCellWidget(row_count, 0, checkbox)  # Assuming checkbox is in the first column

                for col, data in enumerate(row):
                    item = QTableWidgetItem(data)
                    self.table.setItem(row_count, col + 1, item)  # Offset column index

                    if col == 0:  # Assuming system name is in the second column
                        self.system_name.append(item)
                    elif col == 1:  # Assuming entry point is in the third column
                        self.entry_point.append(item)
                    # elif col == 3:  # Assuming last scan time is in the fourth column
                    #     self.last_scan_time.append(item)

    def save_config(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = str(self.program_settings_file_path) + f".{timestamp}" + ".bak"

        if os.path.exists(self.program_settings_file_path):
            # Create a backup copy
            try:
                os.rename(self.program_settings_file_path, backup_path)
                print(f"Backup created: {backup_path}")
            except OSError as e:
                QMessageBox.warning(self, "Error", f"Failed to create backup: {e}")
                return

        with open(self.program_settings_file_path, "wb") as f:
            settings = []
            for job_index in range(len(self.system_name)):
                if not self.checkboxes[job_index].isChecked():  # do not save unchecked line
                    continue
                this_line = {
                    'checked': True,
                    'system_name': self.system_name[job_index].text(),
                    'entry_point': self.entry_point[job_index].text(),
                    'last_scan_time': "NEVER",
                }
                settings.append(this_line)
            pickle.dump(settings, f)
        QMessageBox.information(self, "Done", f"Saved {len(settings)} rows")
        print("Settings saved successfully!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = CSVViewer()
    viewer.show()
    sys.exit(app.exec())
