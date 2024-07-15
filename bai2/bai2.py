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

response_body_index = f'''
<html>
<head>  
    <title>Download Page</title>
    <style>
        body {{
            background-image: url('/static/background.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            min-height: 100vh;
        }}
        .button-container {{
            margin-top: auto;
            margin-bottom: 20px;
        }}
        .download-button {{
            padding: 15px 30px;
            font-size: 24px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        .download-button:hover {{
            background-color: #45a049;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #666;
        }}
    </style>
    <script>
        function redirectToDownloadPage() {{
            window.location.href = '/download';
        }}
    </script>
</head>
<body>
    <h1 style="text-align: center;">Download List</h1>
    <div class="button-container">
        <button class="download-button" onclick="redirectToDownloadPage()">Download List</button>
    </div>
</body>
</html>
'''

response_body_download = '''
<html>
<head>  
    <title>Download List</title>
    <style>
        body {{
            background-image: url('/static/kobt.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            width: 80%;
            margin: 20px auto;
            background-color: #f2f2f2;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}
        .file-list {{
            list-style-type: none;
            padding: 0;
        }}
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #fff;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }}
        .file-name {{
            flex: 1;
            text-align: left; /* Căn trái */
            padding-right: 10px;
        }}
        .file-size {{
            flex: 0 0 150px;
            text-align: right; /* Căn phải */
        }}
        a {{
            text-decoration: none;
            color: #333;
        }}
        .header {{
            text-align: center;
            margin-bottom: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">Download List</h1>
        <ul class="file-list">
            {file_list}
        </ul>
    </div>
</body>
</html>
'''

def list_files_html(): 
    files = os.listdir(DICTIONARY) 
    file_list_html = '' 
    for file in files: 
        file_path = os.path.join(DICTIONARY, file) 
        file_size = os.path.getsize(file_path) 
        file_list_html += f'''
            <li class="file-item">
                <span class="file-name"><a href="/download?file={file}">{file}</a></span>
                <span class="file-size">{file_size} bytes</span>
            </li>
        '''
    return file_list_html.strip()

def handle_request(request): # Handle request
    headers = request.split('\r\n') # Split request into lines
    request_line = headers[0] # First line is request line
    method, path, _ = request_line.split()

    if path == '/': 
        response_body = response_body_index
        response = (
            'HTTP/1.1 200 OK\r\n'
            'Content-Type: text/html\r\n'
            'Content-Length: {}\r\n'
            'Connection: close\r\n'
            '\r\n'
            '{}'
        ).format(len(response_body), response_body)
    elif path.startswith('/download'):
        query = {}
        if '?' in path:
            query_string = path.split('?', 1)[1]
            pairs = query_string.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    query[key] = value
                else:
                    query[pair] = ''
        file_name = query.get('file', None)
        if file_name:
            file_path = os.path.join(DICTIONARY, file_name)
            if os.path.exists(file_path):
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
            # Determine content type based on file extension
            content_type = 'application/octet-stream'
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
    if isinstance(response, str): # Check if response is a string
        response = response.encode(FORMAT)
    client_socket.sendall(response)
    client_socket.close()

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(ADDR)
    server_socket.listen()
    print(f'Serving on http://{HOST}:{PORT}')
        
    while True: 
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

run_server()
