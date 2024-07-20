## CIP Inventory Resource Tracker

This Python application provides a graphical user interface (GUI) for managing and tracking resources within a ControlNet (CN) environment. It enables users to:

- **Add new systems:** Specify system names and IP addresses, initiate scans to discover ControlNet modules, and configure deep scans.
- **Manage system entries:** Check and uncheck systems for scanning, delete entries, and view last scan timestamps.
- **Scan selected systems:** Initiate scans for selected systems, monitor progress, and view results in a log.
- **View collected data:** Access and analyze collected data from previous scans in a separate data preview window.

### Features

- **GUI-driven:** Intuitive and user-friendly interface for managing system entries and initiating scans.
- **Multi-threaded:** Utilizes threading to perform scans in the background, ensuring a responsive user experience.
- **ControlNet discovery:** Enables the discovery and analysis of ControlNet modules within the specified system.
- **Data preview:** Provides a dedicated window for browsing and analyzing data collected from scans.
- **Configuration persistence:** Saves user-defined system configurations for future use.

### Getting Started

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/CIP-Inventory-Resource-Tracker.git
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python main.py
```

### Usage

1. **Add a system:**
   - Click the "Add System" button.
   - Enter the system name and IP address in the respective fields.
   - Optionally, check the "Deep scan" box for more comprehensive discovery.
   - Click the "Start scan" button to begin the scan.
   - Click the "Add" button to save the entry.

2. **Manage system entries:**
   - Check or uncheck the checkboxes next to each system to select or deselect them for scanning.
   - Click the "Delete" button next to an entry to remove it.
   - View the last scan time for each system.

3. **Scan selected systems:**
   - Ensure the "Ping IP addresses" checkbox is enabled for initial ping checks.
   - Click the "SCAN" button to initiate scans for selected systems.
   - Monitor progress in the log display.

4. **View collected data:**
   - Click the "View" button to open a separate data preview window.
   - Use the data preview window to filter, sort, and analyze collected data.

### Requirements

- Python 3.x
- PyQt6
- pandas
- icecream (optional, for debugging)

### Dependencies

- `scanner.py`: This module handles the ControlNet scanning process. It should contain a class named `PreScaner` that performs the scan operation and emits signals for progress, errors, and found modules.
- `ip_addr_widget.py`: This module provides custom widgets for entering system names and IP addresses. It should contain the `IPAddressWidget` and `SystemNameWidget` classes.
- `ping_widget.py`: This module provides a widget for pinging IP addresses. It should contain the `PingWidget` class.
- `global_data.py`: This module handles storing and retrieving scanned data.
- `preview_data.py`: This module contains the `DataPreviewWidget` class that enables browsing and analyzing collected data.

### Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests.

### License

This project is licensed under the MIT License.

This README provides a starting point for your project. Feel free to customize it with specific details, instructions, and information relevant to your application.
