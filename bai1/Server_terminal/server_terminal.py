import os
import socket

HOST = socket.gethostbyname(socket.gethostname())
PORT = 12345
ADDR = (HOST, PORT)
DICTIONARY = "files"
FORMAT = 'utf-8'

def list_files():
    return os.listdir(DICTIONARY)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)
server_socket.listen(1)
print("Server is listening...")

while True:
    client_socket, client_addr = server_socket.accept()
    print(f"Connected by {client_addr}")

    files = list_files()
    files_with_sizes = [f"{file}:{os.path.getsize(os.path.join(DICTIONARY, file))}" for file in files]
    client_socket.sendall('\n'.join(files_with_sizes).encode(FORMAT))

    requested_file = client_socket.recv(1024).decode(FORMAT)
    if requested_file in files:
        with open(os.path.join(DICTIONARY, requested_file), 'rb') as f:
            file_data = f.read()
            client_socket.sendall(file_data)

    client_socket.close()
