import os
import socket

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
DICTIONARY = "files"
FORMAT = 'utf-8'
BUFFER_SIZE = 4096

def list_files():
    return os.listdir(DICTIONARY) 

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)
server_socket.listen(1)
print("Server is listening...")
print(f"Server is running on {HOST}, {PORT}")

sent_file_lists = []  

def client_has_received_list(client_addr):
    return any(addr == client_addr for addr in sent_file_lists)

while True:
    client_socket, client_addr = server_socket.accept()
    print(f"Connected by {client_addr}")

    if not client_has_received_list(client_addr[0]):
        sent_file_lists.clear()
        files = list_files()
        files_with_sizes = [f"{file}:{os.path.getsize(os.path.join(DICTIONARY, file))}" for file in files]
        client_socket.sendall('\n'.join(files_with_sizes).encode(FORMAT))
        sent_file_lists.append(client_addr[0])

    requested_file = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
    if requested_file in list_files():
        with open(os.path.join(DICTIONARY, requested_file), 'rb') as f:
            file_data = f.read()
            client_socket.sendall(file_data)

    client_socket.close()
