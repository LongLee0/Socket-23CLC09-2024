import socket
import os
import time

# Ý tưởng: Đọc danh sách các file cần tải xuống từ tập tin input.txt
# và thực hiện tải xuống các file đó từ server
# sau đó lưu vào thư mục output
# Nếu file đã được tải xuống sẽ được thêm vào mảng completed_files
# Nếu thêm file mới vào input.txt thì chương trình sẽ chạy lại để tải file mới
# Chương trình sẽ kiểm tra tập tin input.txt sau mỗi 20 giây
# Nếu người dùng nhấn Ctrl+C thì chương trình sẽ dừng

# HOST = "127.0.0.1"
HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432  # Cổng của server
ADDR = (HOST, PORT)
BUFFER_SIZE = 1024
INPUT_FILE = "input.txt"
OUTPUT_DIR = "output"
FORMAT = 'utf-8'

# Mảng lưu trữ tên các file đã tải xuống
completed_files = []

def download_file(file_name):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(ADDR)
        
        request = f"GET /download?file={file_name} HTTP/1.1\r\nHost: {HOST}\r\n\r\n"
        client_socket.sendall(request.encode(FORMAT))
        
        response = client_socket.recv(BUFFER_SIZE)
        headers, file_data = response.split(b'\r\n\r\n', 1)
        headers_lines = headers.decode(FORMAT).split('\r\n')
        content_length = 0

        for line in headers_lines:
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())

        save_path = os.path.join(OUTPUT_DIR, file_name)
        with open(save_path, 'wb') as f:
            f.write(file_data)

            total_received = len(file_data)
            while total_received < content_length:
                chunk = client_socket.recv(BUFFER_SIZE)
                f.write(chunk)
                total_received += len(chunk)
                progress = (total_received / content_length) * 100
                print(f"\rDownloading: {file_name} .... {progress:.2f}%", end='', flush=True)

        print(f"\rDownload completed: {file_name} (100.00%)")
        completed_files.append(file_name)  # Thêm vào mảng các file đã tải xuống
        return True
    except Exception as e: 
        print(f"\rAn error occurred: {e}")
        return False
    finally:
        client_socket.close()
        print("\rClient socket closed.")

def main():
    if not os.path.exists(OUTPUT_DIR): # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(OUTPUT_DIR)

    while True:
        try:
            with open(INPUT_FILE, 'r') as f:
                files_to_download = f.read().splitlines()

            for file_name in files_to_download:
                if file_name not in completed_files:
                    if download_file(file_name):
                        completed_files.append(file_name)  # Thêm vào mảng các file đã tải xuống

            time.sleep(20)  # Chờ 20 giây trước khi kiểm tra lại tập tin input.txt
        except KeyboardInterrupt:
            print("\nClient program terminated by user.")
            break

main()
