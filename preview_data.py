import pickle
import sys
from pprint import pprint

import pandas as pd

from icecream import ic

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTableView,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMenu,
    QHeaderView, QMessageBox, QDialogButtonBox, QComboBox, QGroupBox, QLineEdit, QGridLayout, QCheckBox, QDialog,
)
from PyQt6 import QtGui
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QModelIndex, QAbstractTableModel, QPoint, QSize, pyqtSignal

from global_data import global_data_obj
from saver import get_user_data_path


class ConfigureDialog(QDialog):
    def __init__(self, data_model, parent=None):
        super().__init__(parent)
        # pprint(parent)
        # pprint(self.parent())
        self.setWindowTitle("Configure Data View")
        self.data_model = data_model

        # Main Grid Layout
        main_layout = QGridLayout()

        # Column Visibility and Filter Section
        column_group = QGroupBox("Column Visibility and Filters")
        column_layout = QGridLayout()

        # Create labels, checkboxes, and line edits
        for i, column_name in enumerate(self.data_model._data.columns):
            label = QLabel(column_name)
            check_box = QCheckBox()
            check_box.setChecked(self.parent().column_visibility[i])
            check_box.stateChanged.connect(lambda state, col=i: self.toggle_column_visibility(col, state))
            filter_edit = QLineEdit()
            filter_edit.setText(self.data_model._filters[i])
            filter_edit.textChanged.connect(lambda text, col=i: self.update_filter(col, text))

            column_layout.addWidget(label, i, 0)
            column_layout.addWidget(check_box, i, 1)
            column_layout.addWidget(filter_edit, i, 2)

        column_group.setLayout(column_layout)
        main_layout.addWidget(column_group, 0, 0, 1, 2)

        # Sorting Section
        sorting_group = QGroupBox("Sorting")
        sorting_layout = QHBoxLayout()

        self.sort_column_combo = QComboBox()
        self.sort_column_combo.addItems(self.data_model._data.columns)
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        self.sort_button = QPushButton("Sort")
        self.sort_button.clicked.connect(self.apply_sorting)

        sorting_layout.addWidget(self.sort_column_combo)
        sorting_layout.addWidget(self.sort_order_combo)
        sorting_layout.addWidget(self.sort_button)

        sorting_group.setLayout(sorting_layout)
        main_layout.addWidget(sorting_group, 1, 0, 1, 2)

        # OK and Cancel Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box, 2, 0, 1, 2)

        self.setLayout(main_layout)

    def toggle_column_visibility(self, column_index, state):
        print(state)
        if state == 2:  # show
            self.parent().table_view.showColumn(column_index)
            self.parent().column_visibility[column_index] = True
        if state == 0:  # hide
            self.parent().table_view.hideColumn(column_index)
            self.parent().column_visibility[column_index] = False

        self.data_model.layoutChanged.emit()
        self.data_model.dataChanged.emit(QModelIndex(), QModelIndex())

    def update_filter(self, column_index, text):
        self.data_model._apply_filter(column_index, filter_value=text)
        self.data_model.layoutChanged.emit()
        self.data_model.dataChanged.emit(QModelIndex(), QModelIndex())

    def apply_sorting(self):
        sort_column = self.sort_column_combo.currentText()
        sort_order = self.sort_order_combo.currentText()

        try:
            if sort_order == "Ascending":
                self.data_model.filtered_data.sort_values(by=sort_column, inplace=True, ascending=True)
            else:
                self.data_model.filtered_data.sort_values(by=sort_column, inplace=True, ascending=False)

            self.data_model.layoutChanged.emit()
            self.data_model.dataChanged.emit(QModelIndex(), QModelIndex())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Sorting failed: {e}")


class DataPreviewWidget(QWidget):
    finished = pyqtSignal()

    def __init__(self, data, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Data Viewer")

        # Create the table view and set editability
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        # self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setEditTriggers(QTableView.EditTrigger.AllEditTriggers)  # Allow editing
        # Hide the row headers (vertical header)
        # self.table_view.verticalHeader().setVisible(False)

        # Create the data model
        self.data_model = DataModel(data)
        self.table_view.setModel(self.data_model)

        # Load view settings from file (if exists)
        self.settings_file = get_user_data_path() / "data_preview_settings.pkl"
        # self.column_visibility = [True for _ in range(data.shape[1])]  # init column visibility
        self.load_settings(data.shape[1])

        # Create the "clear filters" button
        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self.clear_filters)

        # Create the "Configure" button
        self.configure_button = QPushButton("Configure")
        self.configure_button.clicked.connect(self.show_configure_dialog)

        # Create labels for row counts
        self.filtered_rows_label = QLabel("Filtered Rows: 0")
        self.total_rows_label = QLabel(f"Total Rows: {data.shape[0]}")

        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.addWidget(self.configure_button)
        top_buttons_layout.addWidget(self.clear_filters_button)

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Preview:"))
        layout.addLayout(top_buttons_layout)
        layout.addWidget(self.table_view)

        # Add row count labels at the bottom
        row_count_layout = QHBoxLayout()
        row_count_layout.addWidget(self.filtered_rows_label)
        row_count_layout.addWidget(self.total_rows_label)
        layout.addLayout(row_count_layout)

        self.setLayout(layout)

        # Connect to dataChanged signal to update filtered rows count
        self.data_model.dataChanged.connect(self.update_filtered_rows_count)

        # Set up context menu for filtering
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

        for column_index, saved_visibility in enumerate(self.column_visibility):
            self.toggle_column_visibility(column_index, saved_visibility)

        for column_index, saved_filter in enumerate(self.data_model._filters):
            self.data_model._apply_filter(column_index, saved_filter)

        # Connect to header section clicked signal to show the column visibility menu
        # self.table_view.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # self.table_view.horizontalHeader().customContextMenuRequested.connect(self.show_column_visibility_menu)

    def show_configure_dialog(self):
        dialog = ConfigureDialog(self.data_model, self)
        dialog.exec()

    def save_column_widths(self):
        """Returns a list of column widths."""
        return [self.table_view.columnWidth(i) for i in range(self.data_model.columnCount(QModelIndex()))]

    def restore_column_widths(self, widths):
        """Restores column widths from a list."""
        for i, width in enumerate(widths):
            if i < self.data_model.columnCount(QModelIndex()):
                self.table_view.setColumnWidth(i, width)

    def save_window_size(self):
        """Returns the current window size."""
        return self.size()

    def restore_window_size(self, size):
        """Restores the window size."""
        if size:
            self.resize(size)

    def load_settings(self, columns_num: int):
        """Loads settings from a pickle file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'rb') as f:
                    settings = pickle.load(f)
                    self.column_visibility = settings.get("column_visibility", [True for _ in range(columns_num)])
                    self.data_model._filters = settings.get("filters", ['' for _ in range(columns_num)])
                    self.restore_column_widths(settings.get("column_widths", []))  # Restore column widths
                    self.restore_window_size(settings.get("window_size"))  # Restore window size
            except (pickle.PickleError, EOFError) as e:
                QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")
                self.column_visibility = [True for _ in range(columns_num)]  # init column visibility
                self.data_model._filters = settings.get("filters", ['' for _ in range(columns_num)])
        else:
            self.column_visibility = [True for _ in range(columns_num)]  # init column visibility
            self.data_model._filters = ['' for _ in range(columns_num)]

    def save_settings(self):
        """Saves settings to a pickle file."""
        settings = {
            "column_visibility": self.column_visibility,
            "filters": self.data_model._filters,
            "column_widths": self.save_column_widths(),  # Save column widths
            "window_size": self.save_window_size()  # Save window size
        }
        try:
            with open(self.settings_file, 'wb') as f:
                pickle.dump(settings, f)
        except pickle.PickleError as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")

    def closeEvent(self, event):
        self.save_settings()  # Save settings before closing
        self.finished.emit()
        super().closeEvent(event)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        index = self.table_view.indexAt(pos)
        # Don't show context menu for filter row
        if index.row() > 0:
            # Get the cell value
            cell_value = self.data_model.data(index, Qt.ItemDataRole.DisplayRole)
            filter_action = QAction(f"Filter by '{cell_value}'", self)

            filter_action.triggered.connect(
                lambda: self.data_model._apply_filter(index.column(), cell_value)
            )
            menu.addAction(filter_action)

        if self.data_model._filters[index.column()]:
            # if filter for this columnt set already
            drop_filter_action = QAction(f"Drop filter in this column ", self)
            drop_filter_action.triggered.connect(
                lambda: self.data_model._apply_filter(index.column(), '')
            )
            menu.addAction(drop_filter_action)

        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def clear_filters(self):
        self.data_model.clear_filters()

    def update_filtered_rows_count(self, topLeft, bottomRight, roles=None):
        filtered_rows = self.data_model.rowCount(QModelIndex()) - 1  # Exclude filter row
        self.filtered_rows_label.setText(f"Filtered Rows: {filtered_rows}")

    def toggle_column_visibility(self, column_index, visible):
        """Toggles the visibility of the specified column."""
        # self.data_model.column_visibility[column_index] = visible
        header = self.table_view.horizontalHeader()
        if visible:
            # Restore the column's size
            self.table_view.setColumnHidden(column_index, False)

            header.resizeSection(column_index, header.sectionSize(column_index))

        else:
            # Hide the column completely
            header.resizeSection(column_index, 0)  # Set width to 0
            self.table_view.setColumnHidden(column_index, True)

        self.data_model.layoutChanged.emit()
        self.data_model.dataChanged.emit(QModelIndex(), QModelIndex())


class DataModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        # Apply filters to _data
        self.filtered_data = self._data  # no filters now
        self._filters = ['' for _ in range(data.shape[1])]
        # self.column_visibility = [True for _ in range(data.shape[1])]  # init column visibility

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if index.row() == 0:  # First row (filter row) is always editable
            return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsEditable
                    | Qt.ItemFlag.ItemIsSelectable
                # | Qt.ItemFlag.ItemIsDragEnabled
            )
        else:  # All other rows are read-only
            return (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
            )

    def rowCount(self, index):
        return self.filtered_data.shape[0] + 1  # +1 for filter row

    def columnCount(self, index):
        return self._data.shape[1]

    def data(self, index, role):
        if index.row() == 0 and role == Qt.ItemDataRole.DisplayRole:
            value = self._filters[index.column()]
            return str(value)
        elif role == Qt.ItemDataRole.DisplayRole:
            # Handle out-of-bounds index
            if index.row() - 1 < len(self.filtered_data):
                value = self.filtered_data.iloc[index.row() - 1, index.column()]
                if value is None:
                    return ""
                if pd.isna(value):
                    return ""
                if isinstance(value, (int, float)):
                    return f"{value:.0f}"  # Format integers as integers
                return str(value)
            else:
                return ""  # Or return None if you prefer

        # Ensure EditRole is only for the filter row
        if role == Qt.ItemDataRole.EditRole and index.row() == 0:
            value = self._filters[index.column()]
            return str(value)
        if role == Qt.ItemDataRole.BackgroundRole and index.row() == 0:
            # See below for the data structure.
            return QtGui.QColor('lightblue')

        return None

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole and index.row() == 0:
            self._apply_filter(index.column(), value)
            return True
        return False

    def _apply_filter(self, column_index: int, filter_value: str):
        """Applies a filter to the specified column."""
        self._filters[column_index] = filter_value
        self.filtered_data = self._data.copy()  # Reset filtered data

        for i, filter_value in enumerate(self._filters):
            if filter_value:
                # Split filter values by space and apply OR logic
                filter_terms = filter_value.split()
                if filter_terms:
                    filter_mask = False
                    for term in filter_terms:
                        filter_mask = filter_mask | self.filtered_data.iloc[:, i].astype(str).str.contains(term,
                                                                                                           case=False)
                    self.filtered_data = self.filtered_data[filter_mask]

        self.layoutChanged.emit()
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def clear_filters(self):
        self._filters = ['' for _ in range(self._data.shape[1])]
        self.filtered_data = self._data  # Reset filtered data
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                if section == 0:  # Header for filter row
                    return "Filters -->"
                elif section > 0:  # Headers for data rows
                    return str(self.filtered_data.index[section - 1])
        # filtered by value in this column highlighted
        elif role == Qt.ItemDataRole.BackgroundRole and orientation == Qt.Orientation.Horizontal:
            if self._filters[section]:
                return QtGui.QColor("lightgrey")
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)

    import pandas as pd
    import random
    import string


    def generate_test_data(num_rows=5, num_cols=3, max_string_length=10):
        """
        Generates test data for the DataPreviewWidget.

        Args:
        num_rows: Number of rows in the DataFrame.
        num_cols: Number of columns in the DataFrame.
        max_string_length: Maximum length of random strings in each cell.

        Returns:
        A Pandas DataFrame with test data.
        """

        data = []
        for _ in range(num_rows):
            row = []
            for _ in range(num_cols):
                random_string = ''.join(
                    random.choices(string.ascii_letters + string.digits, k=random.randint(1, max_string_length))
                )
                row.append(random_string)
            data.append(row)

        df = pd.DataFrame(
            data, columns=[f"Column_{i + 1}" for i in range(num_cols)], index=[f"Row {i + 1}" for i in range(num_rows)]
        )
        return df


    # Sample data
    data = generate_test_data(num_rows=10000, num_cols=20, max_string_length=2)  # Generate 10 rows, 10 columns

    # # load data
    # test_labor = get_user_data_path() / "labor1.data"
    # global_data = global_data_obj(fname=test_labor)
    # global_data.restore_data()
    # data = pd.DataFrame.from_dict(global_data.module, orient='index')

    preview_widget = DataPreviewWidget(data)
    preview_widget.show()

    sys.exit(app.exec())
