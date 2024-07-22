import socket
import os 
import threading

# HOST = "127.0.0.1"
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
ADDR = (HOST, PORT)
DICTIONARY = "files"
STATIC_DIR = "static"
FORMAT = 'utf-8'

with open(os.path.join('static','response_body_index.html'), 'r', encoding=FORMAT) as file:
    response_body_index = file.read()

with open(os.path.join('static','response_body_download.html'),'r',encoding=FORMAT) as file:
    response_body_download =file.read()

def list_files_html(): # Biến danh sách file thành HTML
    files = os.listdir(DICTIONARY)  # Lấy danh sách file trong thư mục DICTIONARY
    file_list_html = '' # Khởi tạo biến lưu trữ HTML
    for file in files: # Duyệt từng file
        file_path = os.path.join(DICTIONARY, file) # Tạo đường dẫn
        file_size = os.path.getsize(file_path) # Lấy file size
        file_list_html += f''' 
            <li class="file-item">
                <span class="file-name"><a href="/download?file={file}">{file}</a></span>
                <span class="file-size">{file_size} bytes</span>
            </li>
        ''' # Thêm thông tin file vào HTML
    return file_list_html.strip() # strip() để loại bỏ khoảng trắng ở đầu và cuối chuỗi

def handle_request(request): 
    headers = request.split('\r\n') 
    # cấu trúc các dòng trong request: method path version, header1, header2, ... 
    # split('\r\n') là tách request thành các dòng
        
    request_line = headers[0]  
    # Ví dụ cấu trúc request line: GET /path/to/resource HTTP/1.1
    
    method, path, version = request_line.split() # Tách request line thành method, path, version
    
    if path == '/': 
        response = (
            'HTTP/1.1 200 OK\r\n'
            'Content-Type: text/html\r\n'
            'Content-Length: {}\r\n'
            'Connection: close\r\n'
            '\r\n'
            '{}'
        ).format(len(response_body_index), response_body_index)
# Nếu path chỉ là '/' tức là chưa có đường dẫn cụ thể thì trả về trang chính
# Cấu trúc response: status code, content type, content length, connection, \r\n\r\n
# \r\n\r\n để ngăn cách giữa header và body

    elif path.startswith('/download'):
        query = {} 
        if '?' in path: # ví dụ path có dạng /download?file=hello.txt
            query_string = path.split('?', 1)[1] 
            # ,1 là số lần tách tối đa là 1, [1] là lấy phần sau dấu ?
            # ví dụ query_string : file=hello.txt hoặc param1=value1&param2=value2&param3=value3
            pairs = query_string.split('&') 
            # ví dụ pairs: ['file=hello.txt'] hoặc ['param1=value1', 'param2=value2', 'param3=value3']
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1) 
                    # tách 1 lần là tránh trường hợp param=value1=value2
                    query[key] = value
                else:
                    query[pair] = ''
        file_name = query.get('file', None) 
        if file_name: # Nếu file_name tồn tại thì download file 
            file_path = os.path.join(DICTIONARY, file_name) # Tạo đường dẫn tới file_name
            if os.path.exists(file_path): # Nếu file tồn tại thì trả về file
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                file_size = len(file_data)
                response_headers = (
                    'HTTP/1.1 200 OK\r\n'
                    'Content-Type: application/octet-stream\r\n'
                    'Content-Disposition: attachment; filename="{}"\r\n'
                    'Content-Length: {}\r\n'
                    'Connection: close\r\n'
                    '\r\n'
                ).format(file_name, file_size)
                response = response_headers.encode() + file_data
            else: # Nếu file không tồn tại thì trả về 404
                response_body = 'File not found'
                response = (
                    'HTTP/1.1 404 Not Found\r\n'
                    'Content-Type: text/plain\r\n'
                    'Content-Length: {}\r\n'
                    'Connection: close\r\n'
                    '\r\n'
                    '{}'
                ).format(len(response_body), response_body)
        else: # Nếu không có file_name thì trả về trang download tức là chỉ tới path /download
            files_list = list_files_html()
            response_body = response_body_download.format(file_list=files_list)
            response = (
                'HTTP/1.1 200 OK\r\n'
                'Content-Type: text/html\r\n'
                'Content-Length: {}\r\n'
                'Connection: close\r\n'
                '\r\n'
                '{}'
            ).format(len(response_body), response_body)
    elif path.startswith('/static/'):
        static_file_path = os.path.join(STATIC_DIR, path.lstrip('/static/')) 
        if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
            with open(static_file_path, 'rb') as file:
                static_file_data = file.read()
            static_file_size = len(static_file_data)
            # xác định content type dựa vào đuôi file
            content_type = 'application/octet-stream' 
            # application/octet-stream là dạng giữ liệu không biết nghĩa là gì cũng được
            if static_file_path.endswith('.css'):
                content_type = 'text/css'
            elif static_file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif static_file_path.endswith('.jpg') or static_file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif static_file_path.endswith('.png'):
                content_type = 'image/png'
            
            response_headers = (
                'HTTP/1.1 200 OK\r\n'
                'Content-Type: {}\r\n'
                'Content-Length: {}\r\n'
                'Connection: close\r\n'
                '\r\n'
            ).format(content_type, static_file_size)
            response = response_headers.encode() + static_file_data
        else:
            response_body = 'File not found'
            response = (
                'HTTP/1.1 404 Not Found\r\n'
                'Content-Type: text/plain\r\n'
                'Content-Length: {}\r\n'
                'Connection: close\r\n'
                '\r\n'
                '{}'
            ).format(len(response_body), response_body)
    else:
        response_body = 'Page not found'
        response = (
            'HTTP/1.1 404 Not Found\r\n'
            'Content-Type: text/plain\r\n'
            'Content-Length: {}\r\n'
            'Connection: close\r\n'
            '\r\n'
            '{}'
        ).format(len(response_body), response_body)

    return response

def handle_client(client_socket): 
    request = client_socket.recv(1024).decode(FORMAT)
    response = handle_request(request)
    if isinstance(response, str): 
        response = response.encode(FORMAT)
    client_socket.sendall(response)
    client_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(ADDR)
server_socket.listen()
print(f'Serving on http://{HOST}:{PORT}')
        
while True: 
    client_socket, client_address = server_socket.accept()
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()

