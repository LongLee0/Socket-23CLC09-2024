import os
import socket
import tkinter as tk
from tkinter import messagebox, scrolledtext
from threading import Thread
import signal

HOST = socket.gethostbyname(socket.gethostname())
PORT = 12345
FORMAT = 'utf-8'
ADDR = (HOST, PORT)
BUFFERSIZE = 4096

OUTPUT_DIR = 'output'

class FileDownloadClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Download Client")
        self.geometry("600x400")
        self.configure(bg='black')

        self.available_files = []
        self.downloaded_files = set()

        self.create_widgets()
        self.get_file_list()

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Bind Ctrl+C to the on_exit function
        self.bind('<Control-c>', self.on_exit)

        # Set up the signal handler for SIGINT (Ctrl+C in terminal)
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.check_for_exit()

    def create_widgets(self):
        # Create and place file list display
        self.file_list_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, bg='gainsboro', fg='black', font=('Times New Roman', 14))
        self.file_list_display.place(relwidth=1, relheight=0.6)

        # Create and place input for file names
        self.file_entry_label = tk.Label(self, text="Enter file names to download (comma-separated):", bg='white', fg='black', font=('Times New Roman', 14))
        self.file_entry_label.place(rely=0.65, relwidth=1)

        self.file_entry = tk.Entry(self, bg='lavender', fg='black')
        self.file_entry.place(relwidth=1, rely=0.75)

        # Create and place download button
        self.download_button = tk.Button(self, text="Download", command=self.download_files, bg='white', font=('Times New Roman', 14))
        self.download_button.place(relx=0.455, rely=0.82)

        # Create and place progress display
        self.progress_display = tk.Label(self, text="", bg='gainsboro', fg='black', font=('Times New Roman', 14))
        self.progress_display.place(rely=0.9, relwidth=1)

    def get_file_list(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(ADDR)
                client_socket.sendall("GET_FILE_LIST".encode(FORMAT))
                
                file_list_data = b""
                while True:
                    data = client_socket.recv(BUFFERSIZE)
                    if not data:
                        break
                    file_list_data += data

                file_list_str = file_list_data.decode(FORMAT)
                self.available_files = file_list_str.split('\n')
                self.display_file_list()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def display_file_list(self):
        self.file_list_display.delete(1.0, tk.END)
        for file_info in self.available_files:
            if file_info:
                file_name, file_size = file_info.split(':')
                formatted_name = f"{file_name: <30}"
                self.file_list_display.insert(tk.END, f"Filename: {formatted_name} Size: {file_size.strip()} bytes\n")

    def download_files(self):
        file_names = self.file_entry.get().split(',')
        file_names = [file_name.strip() for file_name in file_names if file_name.strip()]
        
        unavailable_files = [file_name for file_name in file_names if not any(file_name == file_info.split(':')[0] for file_info in self.available_files)]
        if unavailable_files:
            unavailable_str = ', '.join(unavailable_files)
            messagebox.showwarning("File Not Found", f"The following files are not available: {unavailable_str}")
            return
        
        file_names = [file_name for file_name in file_names if file_name not in self.downloaded_files]
        
        if file_names:
            self.download_file(file_names, 0)

    def download_file(self, file_names, index):
        if index >= len(file_names):
            return

        file_name = file_names[index]
        def download():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.connect(ADDR)
                    client_socket.sendall(file_name.encode(FORMAT))
                    
                    with open(os.path.join(OUTPUT_DIR, file_name), 'wb') as f:
                        while True:
                            data = client_socket.recv(BUFFERSIZE)
                            if not data:
                                break
                            f.write(data)
                            downloaded_size = os.path.getsize(os.path.join(OUTPUT_DIR, file_name))
                            self.update_progress(file_name, downloaded_size)
                
                self.downloaded_files.add(file_name)
                self.update_progress(file_name, os.path.getsize(os.path.join(OUTPUT_DIR, file_name)), final=True)
                messagebox.showinfo("Download Complete", f"The file '{file_name}' has been downloaded successfully.")
                self.download_file(file_names, index + 1)
            except Exception as e:
                messagebox.showerror("Download Error", str(e))

        Thread(target=download).start()

    def update_progress(self, file_name, downloaded_size, final=False):
        for file_info in self.available_files:
            if file_info.startswith(file_name):
                total_size = int(file_info.split(':')[1])
                progress = 100 if final else (downloaded_size / total_size) * 100
                self.progress_display.config(text=f"Downloading {file_name}: {progress:.2f}%")
                break

    def on_exit(self, event=None):
        self.quit()

    def handle_sigint(self, signal, frame):
        self.on_exit()

    def check_for_exit(self):
        self.after(100, self.check_for_exit)

if __name__ == "__main__":
    app = FileDownloadClient()
    app.mainloop()
