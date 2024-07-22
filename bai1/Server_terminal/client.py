import socket
import os
import time

HOST = socket.gethostbyname(socket.gethostname())
PORT = 12345
ADDR = (HOST, PORT)
BUFFER_SIZE = 1024
INPUT_FILE = "input.txt"
OUTPUT_DIR = "output"
FORMAT = 'utf-8'

completed_files = []

def list_files_to_download():
    try:
        with open(INPUT_FILE, 'r') as f:
            return f.read().splitlines() 
    except FileNotFoundError:
        return []

def download_file(file_name, file_size):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        
        client_socket.sendall(file_name.encode(FORMAT))
        
        save_path = os.path.join(OUTPUT_DIR, file_name)
        with open(save_path, 'wb') as f:
            total_received = 0
            while True:
                file_data = client_socket.recv(BUFFER_SIZE)
                if not file_data:
                    break
                f.write(file_data)
                total_received += len(file_data)

                progress = (total_received / file_size) * 100
                progress = min(progress, 100) 
                print(f"\rDownloading {file_name}... {progress:.2f}%", end='', flush=True)
        
        print(f"\nDownload completed: {file_name}")
        completed_files.append(file_name) 
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    finally:
        client_socket.close()

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(ADDR)
    
    files_info = client_socket.recv(BUFFER_SIZE).decode(FORMAT).split('\n')
    files = {file.split(':')[0]: int(file.split(':')[1]) for file in files_info if ':' in file}

    print("Available files:")
    for file, size in files.items():
        print(f"{file} ({size} bytes)")
    
    client_socket.close()
    
    while True:
        files_to_download = list_files_to_download()

        for file_name in files_to_download:
            if file_name in completed_files:
                continue 

            if file_name in files:
                download_file(file_name, files[file_name])
            else:
                print(f"File {file_name} not available.")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nClient has pressed Ctrl+C. Closing connection...")
