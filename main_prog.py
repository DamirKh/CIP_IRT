import subprocess
import time
from pprint import pprint

import pandas as pd

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QCheckBox,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QSizePolicy,
    QLineEdit,
    QMessageBox,
    QDialog,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt, QThreadPool

# from icecream import ic

import sys
import os
import pathlib
import datetime
import pickle
from pathlib import Path

from add_system import AddSystemDialog, EditSystemDialog
from ping_widget import PingWidget
from log_widget import LogWidget

from version import rev
from saver import get_user_data_path
# from scanner import PreScaner as Scaner
from scanner import Scaner
import global_data
from global_data import global_data_cls

import preview_data

from user_data import basedir, asset_dir
from cog_widget import CogWidget


def load_data(path):
    """Loads data from all files with "*.data" extension in the specified path.

  Args:
    path: The path to the directory containing the data files.

  Returns:
    A pandas DataFrame containing the combined data from all files.
  """

    # Get a list of all files with "*.data" extension in the path
    data_files = [f for f in os.listdir(path) if f.endswith(".data")]

    # Create an empty list to store the DataFrames
    data_frames = []

    # Iterate through each data file and load the data
    for file in data_files:
        # Create the full file path
        file_path = os.path.join(path, file)

        # Load data from the file
        global_data_obj = global_data_cls(fname=file_path)
        global_data_obj.restore_data()
        df = pd.DataFrame.from_dict(global_data_obj.module, orient='index')

        # Append the DataFrame to the list
        data_frames.append(df)

    # Concatenate the list of DataFrames into a single DataFrame
    data = pd.concat(data_frames, ignore_index=False)

    # adding comments
    fname = get_user_data_path() / 'comments.txt'
    comments = global_data.comment_saver_cls(fname=fname)
    comments.load()
    global_data.current_comment_saver = comments

    data['comment'] = list('' for _ in range(len(data.index)))
    # debug injection  001aa5ef
    # global_data.current_comment_saver.set_comment('001aa5ef', 'This is a comment for BP 001aa5ef')

    data['comment'] = data['serial'].map(comments.get_comment).fillna(data['comment'])

    return data


class MainWindow(QWidget):
    def __init__(self):

        super().__init__()

        # self.running_scanner = None
        self.setWindowTitle("CIP Inventory Resource Tracker")
        self.resize(800, 600)

        # Program settings file
        self.program_settings_file_path = get_user_data_path() / f"main_prog.cfg"

        # Initial widgets (start with one row)
        self.system_name = []
        self.entry_point = []
        self.last_scan_time = []
        self.ping_status = []
        self.preview_buttons = []
        self.checkboxes = []
        self.delete_buttons = []
        self.log_buttons = []

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.view_data_window = None

        if True:
            # Create layout
            self.grid_layout = QGridLayout()
            # Create a QWidget to hold the grid layout
            self.grid_widget = QWidget()  # Assign to self.grid_widget
            self.grid_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.grid_widget.setLayout(self.grid_layout)

            # Create a scroll area and add the grid widget to it
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidget(self.grid_widget)
            self.scroll_area.setWidgetResizable(True)

            # Create a spacer widget and set its size policy to expand Vertically
            self.spacer = QWidget()
            self.spacer.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

            # Add labels for grid
            row_index = 0
            self.top_checkbox = QCheckBox()
            self.ping_checkbox = QCheckBox('Ping IP addresses')
            # self.ping_checkbox.setDisabled(True)
            self.grid_layout.addWidget(self.top_checkbox, row_index, 0)
            self.grid_layout.addWidget(QLabel("System name"), row_index, 1)
            self.grid_layout.addWidget(QLabel("Entry point"), row_index, 3)
            self.grid_layout.addWidget(self.ping_checkbox, row_index, 4)
            self.grid_layout.addWidget(QLabel("Last scan time"), row_index, 5)

            # Connect top checkbox to other checkboxes
            self.top_checkbox.stateChanged.connect(self.top_checkbox_changed)

            self.ping_checkbox.stateChanged.connect(self.ping_checkbox_changed)

            # Set spacing for better visual separation
            self.grid_layout.setHorizontalSpacing(5)
            self.grid_layout.setVerticalSpacing(5)

            # Set layout for the main window
            main_layout = QVBoxLayout(self)
            top_buttons = QWidget()
            top_buttons.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            main_layout.addWidget(top_buttons, stretch=0)

            # set layout for top buttons
            top_layout = QHBoxLayout(top_buttons)
            # top_buttons.setLayout(top_layout)

            # Add a button to add new rows
            self.add_row_button = QPushButton("Add System")
            self.add_row_button.setIcon(
                QIcon(os.path.join(asset_dir, "add.png")))
            self.add_row_button.setIconSize(QSize(32, 32))
            self.add_row_button.setToolTip("Add system")
            self.add_row_button.setText("")
            self.add_row_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.add_row_button.clicked.connect(self.add_row)
            top_layout.addWidget(self.add_row_button, stretch=0)

            # Add a button to save config
            self.save_config_button = QPushButton("Save config")
            self.save_config_button.setIcon(
                QIcon(os.path.join(asset_dir, "floppy-disks.png")))
            self.save_config_button.setIconSize(QSize(32, 32))
            self.save_config_button.setToolTip("Save config for future use")
            self.save_config_button.setText("")
            self.save_config_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.save_config_button.clicked.connect(self.save_config)
            top_layout.addWidget(self.save_config_button, stretch=0)

            # Add a button to RUN
            self.run_button = QPushButton("SCAN")
            self.run_button.setIcon(QIcon(os.path.join(asset_dir, "progress-upload.png")))
            self.run_button.setIconSize(QSize(32, 32))
            self.run_button.setToolTip("Scan selected rows")
            self.run_button.setText("")
            self.run_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.run_button.clicked.connect(self.start_scan)
            top_layout.addWidget(self.run_button, stretch=0)

            # Add a button to View
            self.run_button = QPushButton("View")
            self.run_button.setIcon(QIcon(os.path.join(asset_dir, "arrows-to-eye.png")))
            self.run_button.setIconSize(QSize(32, 32))
            self.run_button.setToolTip("View data")
            self.run_button.setText("")
            self.run_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.run_button.clicked.connect(self.view_data)
            top_layout.addWidget(self.run_button, stretch=0)

            # Add a spacer to the right of the top buttons
            spacer_hor = QWidget()
            top_layout.addWidget(spacer_hor, stretch=1)

            # Add cog widget
            self.cog_widget = CogWidget(self.threadpool, os.path.join(asset_dir, "loading.gif"))
            top_layout.addWidget(self.cog_widget, stretch=0)

            # Add a button to show data directory
            self.open_folder_button = QPushButton("Explore data folder")
            self.open_folder_button.setIcon(QIcon(os.path.join(asset_dir, "folder-open-regular.png")))
            self.open_folder_button.setIconSize(QSize(32, 32))
            self.open_folder_button.setToolTip("Open data folder")
            self.open_folder_button.setText("")
            self.open_folder_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.open_folder_button.clicked.connect(self.open_folder)
            top_layout.addWidget(self.open_folder_button, stretch=0)

            # Add a button to show "About" dialog
            self.about_button = QPushButton("About")
            self.about_button.setIcon(QIcon(os.path.join(asset_dir, "information.png")))
            self.about_button.setIconSize(QSize(32, 32))
            self.about_button.setToolTip("About CIP Inventory Resource Tracker")
            self.about_button.setText("")
            self.about_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.about_button.clicked.connect(self.show_about)
            top_layout.addWidget(self.about_button, stretch=0)


            # Add a scrollable grid
            main_layout.addWidget(self.scroll_area, stretch=1)

            # self.setLayout(main_layout)
            self.setMinimumSize(800, 600)

            # Set scroll area size policy to prevent stretching
            self.scroll_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # Load previous settings if available
        saved_configs = self.load_settings()
        if saved_configs:
            self.apply_previous_settings(saved_configs)
        else:
            # Add initial widgets to grid layout
            # self.add_row()
            pass



    def open_folder(self):
        directory_path = get_user_data_path()
        print(f"Opening folder {directory_path}")
        if sys.platform == "win32":
            os.startfile(directory_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", directory_path])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", directory_path])
        else:
            QMessageBox.warning(self, "Error", f"Unsupported platform: {sys.platform}")

    def enable_main_window(self):
        self.setDisabled(False)

    def view_data(self):
        saved_data_path = get_user_data_path()
        data = load_data(saved_data_path)
        self.view_data_window = preview_data.DataPreviewWidget(data)

        # Disable the main window (optional)
        self.setDisabled(True)

        # Show the data preview window
        self.view_data_window.show()

        # **Connect to the 'finished' signal of the data preview window:**
        self.view_data_window.finished.connect(self.enable_main_window)

    def ping_checkbox_changed(self, state):
        print(f'Ping enabled {self.ping_checkbox.checkState()}')
        if state == 2:  # Qt.Checked
            # print('Enable pinging')
            for i, ping_widget in enumerate(self.ping_status):
                ping_widget.start_ping(self.entry_point[i].text())
        elif state == 0:  # Qt.Unchecked
            # print('Disable pinging')
            self.ping_checkbox.setText('Wait...')
            self.ping_checkbox.setEnabled(False)
            for ping_widget in self.ping_status:
                ping_widget.stop_ping()
            self.ping_checkbox.setText('Ping IP addresses')
            self.ping_checkbox.setEnabled(True)

    def start_scan(self):
        if not len(self.system_name):
            QMessageBox.information(self, "No any system selected", f"Please, \nspecify at least one system to scan")
            return
        else:
            for i, current_system in enumerate(self.system_name):
                if not self.checkboxes[i].isChecked():
                    print(f"Skip {current_system.text()}")
                    continue
                try:
                    print(f"Trying to scan {current_system.text()} via {self.entry_point[i].text()}...")
                    running_scanner = Scaner(
                        system_name=current_system.text(),
                        entry_point=self.entry_point[i].text(),
                        finish_callback=self.system_finished,
                        deep_scan=True,
                    )
                    # self.log_buttons[i].start_log()

                    running_scanner.signals.start.connect(self.log_buttons[i].start_log)
                    running_scanner.signals.finished.connect(self.system_finished)
                    running_scanner.signals.progress.connect(self.update_progress)
                    running_scanner.signals.module_found.connect(self.module_found)
                    running_scanner.signals.cn_node_current.connect(self.cn_node_current)
                    running_scanner.signals.communication_error.connect(self.communication_error)
                    self.threadpool.start(running_scanner)
                except SystemExit:
                    print(f"Error scanning {current_system.text()}")
            return


    def system_finished(self, system_name: str):
        print(f'Scan finished: {system_name}')
        # Update the last scan time
        for i, current_system in enumerate(self.system_name):
            if current_system.text() == system_name:
                self.last_scan_time[i].setText(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.log_buttons[i].log('Scan finished')
                self.log_buttons[i].stop_log()
                break

    def communication_error(self, system_name: str):
        print(f'Communication error: {system_name}')
        # Update the last scan time
        for i, current_system in enumerate(self.system_name):
            if current_system.text() == system_name:
                self.last_scan_time[i].setText(f'Error {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                self.log_buttons[i].log(f'Communication Error {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                self.log_buttons[i].stop_log()
                break

    def update_progress(self, system_name: str, message: str):
        print(message)
        # Update progress
        for i, current_system in enumerate(self.system_name):
            if current_system.text() == system_name:
                self.ping_status[i].progress_forward()
                self.log_buttons[i].log(message)
                break

    def module_found(self, module: dict):
        print(f"Module found: {module}")

    def cn_node_current(self, node: str):
        print(f"Current ControlNet node: {node}")

    def load_settings(self):
        """Loads settings from the binary file."""
        if os.path.exists(self.program_settings_file_path):
            try:
                with open(self.program_settings_file_path, "rb") as f:
                    settings = pickle.load(f)
                    print("Loaded settings:", settings)
            except (pickle.PickleError, OSError) as e:
                print(f"Error saving settings: {e}")
                return False
            except EOFError as e:
                print(f"Broken settings file: {e}")
                os.unlink(self.program_settings_file_path)
                print("Deleted!!")
                return False
            return settings
        else:
            print("No settings found.")
            return False

    def save_config(self):
        with open(self.program_settings_file_path, "wb") as f:
            settings = []
            for job_index in range(len(self.system_name)):
                if not self.checkboxes[job_index].isEnabled():  # do not mess with isChecked()
                    continue
                this_line = {
                    'checked': self.checkboxes[job_index].isChecked(),  # 1
                    'system_name': self.system_name[job_index].text(),  # 2
                    'entry_point': self.entry_point[job_index].text(),  # 3
                    'last_scan_time': self.last_scan_time[job_index].text(),
                }
                settings.append(this_line)
            pickle.dump(settings, f)
        QMessageBox.information(self, "Done", f"Saved {len(settings)} rows")
        print("Settings saved successfully!")

    def top_checkbox_changed(self, state):  # Leftmost checkboxes
        # print(f'Top checkbox {state}')
        # Check if top checkbox is checked
        if state == 2:  # Qt.Checked
            for cb in self.checkboxes:
                cb.setChecked(True)
        elif state == 0:  # Qt.Unchecked
            for cb in self.checkboxes:
                cb.setChecked(False)

    def show_preview(self, index):
        """Show preview or delete string"""
        print(f"Not implemented")
        return

    def add_row(self):
        add_system = AddSystemDialog(self, system_names_defined=[_.text() for _ in self.system_name])

        # Connect the signal to the slot
        add_system.data_ready.connect(self.handle_data)

        result = add_system.exec()
        if result != 1:  # due to some bug compare to hardcoded value
            print("Rejected!")
            return

    def edit_row(self, index):
        edit_system = EditSystemDialog(parent=self,
                                       system_name=self.system_name[index].text(),
                                       ip_addr=self.entry_point[index].text())
        edit_system.data_ready.connect(self.update_data)
        result = edit_system.exec()
        if result != 1:  # due to some bug compare to hardcoded value
            print("Update Rejected!")
            return
        else:
            print("Update accepted")
            self.entry_point[index].setText(edit_system.ip_widget.get_ip())


    def delete_row(self, row_index):
        # Remove widgets from the grid layout
        # for i in range(len(self.system_name)):
        #     if i == row_index:
        i = row_index
        self.grid_layout.removeWidget(self.system_name[i])
        self.grid_layout.removeWidget(self.entry_point[i])
        self.grid_layout.removeWidget(self.ping_status[i])
        self.grid_layout.removeWidget(self.last_scan_time[i])
        self.grid_layout.removeWidget(self.preview_buttons[i])
        self.grid_layout.removeWidget(self.checkboxes[i])
        self.grid_layout.removeWidget(self.delete_buttons[i])

        # Remove items from lists
        del self.system_name[i]
        del self.entry_point[i]
        del self.ping_status[i]
        del self.last_scan_time[i]
        del self.preview_buttons[i]
        del self.checkboxes[i]
        del self.delete_buttons[i]
        # break
        # # Update row indices
        # for i in range(row_index, len(self.system_name)):
        #     self.checkboxes[i].setChecked(False)

        # Adjust scroll area size
        self.grid_layout.update()
        self.grid_widget.updateGeometry()
        self.scroll_area.updateGeometry()

    def update_data(self, *args, **kwargs):
        pprint(args)
        pprint(kwargs)

    def handle_data(self, system_name, ip_address, deep_scan=None, checked=False, last_scan_time=None):

        # Receive data and use it to add a row
        # ... (add a row to the grid layout)
        row_index = len(self.system_name) + 1

        # Create new widgets for the row
        self.system_name.append(QLabel(system_name))
        self.entry_point.append(QLabel(ip_address))
        self.ping_status.append(PingWidget(q=4, size=15))
        self.last_scan_time.append(QLabel("UNKNOWN"))
        if last_scan_time:
            self.last_scan_time[-1].setText(str(last_scan_time))  # Checkit!
        # Create Edit button
        self.preview_buttons.append(QPushButton(f"Edit"))
        self.preview_buttons[-1].clicked.connect(lambda: self.edit_row(row_index - 1))
        # self.preview_buttons[-1].setDisabled(True)
        self.log_buttons.append(LogWidget(viewer_title=f"{system_name} scanner log"))

        self.checkboxes.append(QCheckBox())
        self.checkboxes[-1].setChecked(checked)

        # Remove spacer
        # Find the position of the widget in the layout
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item.widget() is self.spacer:
                self.grid_layout.removeItem(item)
                # print(f"Spacer deleted at pos {i}")
                break

        # Add widgets to grid layout
        job_no = row_index - 1
        self.grid_layout.addWidget(self.checkboxes[job_no], row_index, 0)
        self.grid_layout.addWidget(self.system_name[job_no], row_index, 1)
        self.grid_layout.addWidget(self.entry_point[job_no], row_index, 3)
        self.grid_layout.addWidget(self.ping_status[job_no], row_index, 4)
        self.grid_layout.addWidget(self.last_scan_time[job_no], row_index, 5)
        self.grid_layout.addWidget(self.log_buttons[job_no], row_index, 6)

        self.grid_layout.addWidget(self.preview_buttons[job_no], row_index, 7)

        # Create delete button
        self.delete_buttons.append(QPushButton("Delete"))
        self.delete_buttons[-1].clicked.connect(lambda: self.delete_row(row_index - 1))
        self.grid_layout.addWidget(self.delete_buttons[-1], row_index, 8)



        # Add spacer
        self.grid_layout.addWidget(self.spacer, row_index + 1, 0)

        # Set minimum width for the new checkbox
        self.checkboxes[job_no].setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.checkboxes[job_no].setMinimumWidth(20)

        # Adjust scroll area size to accommodate the new row
        self.grid_layout.update()
        self.grid_widget.updateGeometry()
        self.scroll_area.updateGeometry()

        # ... (Any additional adjustments or logic for the new row)

    def apply_previous_settings(self, saved_configs):
        print(f"Apply prev job list...")
        for job in saved_configs:
            self.handle_data(
                checked=job['checked'],
                system_name=job['system_name'],
                ip_address=job['entry_point'],
                last_scan_time=job['last_scan_time']
            )
        pass

    def show_about(self):
        """Show the about dialog."""
        about_dialog = QMessageBox()
        about_dialog.setWindowTitle("About CIP Inventory Resource Tracker")
        about_dialog.setIcon(QMessageBox.Icon.Information)
        about_dialog.setText(f"CIP Inventory Resource Tracker\n\n"
                             f"Version {rev}\n"
                             f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads\n"
                             f"Your data saved here: {get_user_data_path()}\n"
                             )
        about_dialog.setInformativeText("This application is designed for CPC \n"
                                        "by Damir Khakimov (1352)\n")
        about_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        about_dialog.exec()

if __name__ == '__main__':
    # ic(os.name)
    # Get the data path
    data_path = get_user_data_path()
    prev_data_path = data_path / 'prev'

    # Create the directory if it doesn't exist
    if not data_path.exists():
        data_path.mkdir(parents=True, exist_ok=True)
    if not prev_data_path.exists():
        prev_data_path.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(asset_dir, 'irt.ico')))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
