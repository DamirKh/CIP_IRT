import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QTableView,
    QLabel,
    QVBoxLayout
)
from PyQt6.QtCore import Qt, QModelIndex, QAbstractTableModel


class DataPreviewWidget(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)

        # Create the table view and set editability
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setEditTriggers(QTableView.EditTrigger.AllEditTriggers)  # Allow editing

        # Create the data model
        self.data_model = DataModel(data)
        self.table_view.setModel(self.data_model)

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Data Preview:"))
        layout.addWidget(self.table_view)
        self.setLayout(layout)

class DataModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._header_labels = data[0]

    class DataModel(QAbstractTableModel):
        # ... (other methods)

        def flags(self, index: QModelIndex) -> Qt.ItemFlag:
            return (
                    Qt.ItemIsEnabled
                    # | Qt.ItemIsSelectable
                    | Qt.Editable
                    # | Qt.ItemIsDropEnabled  # Enable dropping
            )

        # ... (other methods)
    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data) - 1

    def columnCount(self, parent: QModelIndex = ...) -> int:
        if self._data:
            return len(self._data[0])
        else:
            return 0

    def data(self, index: QModelIndex, role: int = ...) -> object:
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row() + 1
            column = index.column()
            return self._data[row][column]

        if role == Qt.ItemDataRole.EditRole:
            row = index.row() + 1
            column = index.column()
            return self._data[row][column]

    def setData(self, index: QModelIndex, value, role: int = ...) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            row = index.row() + 1
            column = index.column()
            self._data[row][column] = value
            self.dataChanged.emit(index, index)  # Signal data change
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> object:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._header_labels[section]
            else:
                return f"Row {section + 1}"

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sample data
    data = [
        ["Name", "Age", "City"],
        ["John Doe", 30, "New York"],
        ["Jane Doe", 25, "London"],
        ["Peter Pan", 10, "Neverland"],
    ]

    preview_widget = DataPreviewWidget(data)
    preview_widget.show()

    sys.exit(app.exec())