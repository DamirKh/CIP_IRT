import sys

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
    QHeaderView,
)
from PyQt6 import QtGui
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QModelIndex, QAbstractTableModel, QPoint, QSize

from global_data import global_data

class DataPreviewWidget(QWidget):
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

        # Create the "clear filters" button
        self.clear_filters_button = QPushButton("Clear Filters")
        self.clear_filters_button.clicked.connect(self.clear_filters)

        # Create labels for row counts
        self.filtered_rows_label = QLabel("Filtered Rows: 0")
        self.total_rows_label = QLabel(f"Total Rows: {data.shape[0]}")

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Preview:"))
        layout.addWidget(self.clear_filters_button)
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

        # Connect to header section clicked signal to show the column visibility menu
        self.table_view.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.horizontalHeader().customContextMenuRequested.connect(self.show_column_visibility_menu)

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

    def show_column_visibility_menu(self, pos):
        """Shows a menu to toggle column visibility."""
        index = self.table_view.indexAt(pos)
        if index.isValid():

            menu = QMenu(self)
            column_name = self.data_model.headerData(index.column(), Qt.Orientation.Horizontal,
                                                     Qt.ItemDataRole.DisplayRole)
            ic(index.column())
            ic(column_name)
            if self.data_model.column_visibility[index.column()]:
                # Column is visible, create an action to hide it
                hide_action = QAction(f"Minimize '{column_name}'", self)
                hide_action.triggered.connect(lambda: self.toggle_column_visibility(index.column(), False))
                menu.addAction(hide_action)
            else:
                # Column is hidden, create an action to show it
                show_action = QAction(f"Restore '{column_name}'", self)
                show_action.triggered.connect(lambda: self.toggle_column_visibility(index.column(), True))
                menu.addAction(show_action)

            # menu.exec(self.table_view.viewport().mapToGlobal(self.table_view.horizontalHeader().mapToGlobal(QPoint(index.column() * self.table_view.horizontalHeader().sectionSize(logicalIndex), 0))))
            menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def clear_filters(self):
        self.data_model.clear_filters()

    def update_filtered_rows_count(self, topLeft, bottomRight, roles=None):
        filtered_rows = self.data_model.rowCount(QModelIndex()) - 1  # Exclude filter row
        self.filtered_rows_label.setText(f"Filtered Rows: {filtered_rows}")

    def toggle_column_visibility(self, column_index, visible):
        """Toggles the visibility of the specified column."""
        self.data_model.column_visibility[column_index] = visible
        header = self.table_view.horizontalHeader()
        if visible:
            # Restore the column's size
            header.resizeSection(column_index, header.sectionSize(column_index))
        else:
            # Minimize the column
            self.table_view.setColumnWidth(column_index, 5)  # Set to 10 pixels wide
            header.resizeSection(column_index, -5)  # Set to 10 pixels wide
        self.data_model.layoutChanged.emit()
        self.data_model.dataChanged.emit(QModelIndex(), QModelIndex())


class DataModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        # Apply filters to _data
        self.filtered_data = self._data  # no filters now
        self._filters = ['' for _ in range(data.shape[1])]
        self.column_visibility = [True for _ in range(data.shape[1])]  # init column visibility

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
        # If the column is minimized, return an empty string for DisplayRole
        if not self.column_visibility[index.column()] and role == Qt.ItemDataRole.DisplayRole:
            return ''
        if not self.column_visibility[index.column()] and role == Qt.ItemDataRole.SizeHintRole:
            # Ensure the size hint is small enough for the minimized column
            return QSize(5, 0)

        if index.row() == 0 and role == Qt.ItemDataRole.DisplayRole:
            value = self._filters[index.column()]
            return str(value)
        elif role == Qt.ItemDataRole.DisplayRole:
            # Handle out-of-bounds index
            if index.row() - 1 < len(self.filtered_data):
                value = self.filtered_data.iloc[index.row() - 1, index.column()]
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
                if self.column_visibility[section]:
                    return str(self._data.columns[section])
                else:
                    return "*"  # Show a minimal symbol in the header

            if orientation == Qt.Orientation.Vertical:
                if section == 0:  # Header for filter row
                    return "Filter"
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
    # data = generate_test_data(num_rows=10000, num_cols=20, max_string_length=2)  # Generate 10 rows, 10 columns

    # load data
    global_data.restore_data()
    data = pd.DataFrame.from_dict(global_data.module, orient='index')

    preview_widget = DataPreviewWidget(data)
    preview_widget.show()

    sys.exit(app.exec())
