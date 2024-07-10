import subprocess
import platform
import os
import time

def ping(host, packages=1, wait=2):
    """
    Pings a host and returns the exit code (0 for success, non-zero for failure).

    :param str host: The hostname or IP address to ping.
    :param int packages: Number of ping packets to send (default: 4).
    :param int wait: Timeout in seconds (default: 2).
    :return int: The exit code of the ping command.
    """
    system = platform.system()

    # Windows
    if system == "Windows":
        command = ['ping', '-n', str(packages), '-w', str(wait), host]

    # Linux/macOS
    else:
        command = ['ping', '-c', str(packages), '-W', str(wait), host]

    try:
        # Execute the ping command
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode
    except FileNotFoundError:
        print("Error: Ping command not found.")
        return 1
