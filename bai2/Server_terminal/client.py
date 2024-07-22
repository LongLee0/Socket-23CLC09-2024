import socket
import os
import time
import threading
import signal
import sys

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
BUFFER_SIZE = 1024
INPUT_FILE = "input.txt"
OUTPUT_DIR = "output"
FORMAT = 'utf-8'

priority_values = {
    "CRITICAL": 10,
    "HIGH": 4,
    "NORMAL": 1
}

completed_files = []
file_progress = {}  # Dictionary to track progress of each file
stop_threads = False

def signal_handler(sig, frame):
    global stop_threads
    print("\nClient has pressed Ctrl+C. Closing connection...")
    stop_threads = True
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def list_files_to_download():
    try:
        with open(INPUT_FILE, 'r') as f:
            return [line.rsplit(' ', 1) for line in f.read().splitlines()]
    except FileNotFoundError:
        return []

def download_file(file_name, file_size, chunks, priority):
    global stop_threads
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        client_socket.sendall(file_name.encode(FORMAT))

        save_path = os.path.join(OUTPUT_DIR, file_name)
        total_received = 0

        with open(save_path, 'wb') as f:
            while total_received < file_size and not stop_threads:
                file_data = client_socket.recv(BUFFER_SIZE * chunks)
                if not file_data:
                    break
                f.write(file_data)
                total_received += len(file_data)

                # Calculate and update progress
                progress = (total_received / file_size) * 100
                file_progress[file_name] = progress
                print_progress()

        # Ensure final progress update to 100%
        if not stop_threads:
            file_progress[file_name] = 100
            print_progress()
            print(f"\nDownload completed: {file_name}")
            completed_files.append(file_name)

    except Exception as e:
        print(f"Error downloading {file_name}: {e}")

    finally:
        client_socket.close()

def print_progress():
    with print_lock:
        sys.stdout.write("\r")
        for file_name in file_progress:
            progress = file_progress.get(file_name, 0)
            sys.stdout.write(f"{file_name}: {progress:.2f}%  ")
        sys.stdout.flush()

def get_available_files():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        files_info = client_socket.recv(BUFFER_SIZE).decode(FORMAT).split('\n')
        files = {}
        for file in files_info:
            if ':' in file:
                name, size = file.split(':')
                files[name] = int(size)
        client_socket.close()
        return files
    except Exception as e:
        print(f"Error getting available files: {e}")
        return {}

def start_download_threads(files, files_to_download):
    threads = []
    for file_name, priority in files_to_download:
        if stop_threads:
            break

        if file_name in completed_files or file_name not in files:
            continue

        file_size = files[file_name]
        chunks = priority_values.get(priority.upper(), 1)
        thread = threading.Thread(target=download_file, args=(file_name, file_size, chunks, priority.upper()))
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()
        
    # Final progress print after all downloads are complete
    print_progress()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Lock for printing progress to avoid concurrent writes
print_lock = threading.Lock()

try:
    # Print available files only once
    files = get_available_files()
    if files:
        print("Available files:")
        for file, size in files.items():
            print(f"{file} ({size} bytes)")

    while not stop_threads:
        files_to_download = list_files_to_download()
        start_download_threads(files, files_to_download)

        time.sleep(2)

except KeyboardInterrupt:
    print("\nClient has pressed Ctrl+C. Closing connection...")
