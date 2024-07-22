import socket
import os
import time
import threading

# HOST = "127.0.0.1"
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
INPUT_FILE = "input.txt"
OUTPUT_DIR = "output"
CHUNK_SIZE = 1024
FORMAT = 'utf-8'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

completed_files = []

def download_file(file_name, priority):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(ADDR)
        offset = 0
        file_size = None

        with open(os.path.join(OUTPUT_DIR, file_name), 'wb') as output_file:
            while True:
                request = f"GET /download?file={file_name}&offset={offset}&chunk_size={CHUNK_SIZE} HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
                client_socket.sendall(request.encode(FORMAT))
                response = client_socket.recv(4096)
                headers, chunk = response.split(b'\r\n\r\n', 1)
                if not file_size:
                    for header in headers.decode(FORMAT).split('\r\n'):
                        if header.startswith('Content-Length:'):
                            file_size = int(header.split(': ')[1])
                output_file.write(chunk)
                offset += len(chunk)
                percent_complete = (offset / file_size) * 100
                print(f"Downloading {file_name}: {percent_complete:.2f}% complete", end='\r')

                if offset >= file_size:
                    print(f"\nDownload completed: {file_name}")
                    break

        completed_files.add(file_name)

def monitor_input_file():
    while True:
        time.sleep(2)
        with open(INPUT_FILE, 'r') as file:
            for line in file:
                file_name, priority = line.strip().rsplit(' ', 1)
                if file_name not in completed_files:
                    download_file(file_name, priority)

def main():
    input_thread = threading.Thread(target=monitor_input_file)
    input_thread.start()
    input_thread.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Client program terminated by user.")
