import os
import socket
import threading

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
DICTIONARY = "files"
BUFFER_SIZE = 1024
FORMAT = 'utf-8'

def list_files():
    return [(f, os.path.getsize(os.path.join(DICTIONARY, f))) for f in os.listdir(DICTIONARY)]

def handle_client(client_socket):
    files = list_files()
    file_list = '\n'.join(f"{file}:{size}" for file, size in files)
    client_socket.sendall(file_list.encode(FORMAT))

    while True:
        try:
            requested_file = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
            if not requested_file:
                break

            if requested_file in [f[0] for f in files]:
                with open(os.path.join(DICTIONARY, requested_file), 'rb') as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        client_socket.sendall(data)
        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)
server_socket.listen()
print("Server is listening...")

while True:
    client_socket, client_addr = server_socket.accept()
    print(f"Connected by {client_addr}")
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()
