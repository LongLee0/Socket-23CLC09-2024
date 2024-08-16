import socket
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
from threading import Thread, Lock
import signal

HOST = socket.gethostbyname(socket.gethostname())
PORT = 65432
FORMAT = 'utf-8'
ADDR = (HOST, PORT)
BUFFER_SIZE = 4096  

OUTPUT_DIR = 'output'

PRIORITY_VALUES = {
    'CRITICAL': 10,
    'HIGH': 4,
    'NORMAL': 1
}

class FileDownloadClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Download Client")
        self.geometry("600x500")
        self.configure(bg='black')

        self.available_files = []
        self.downloaded_files = set(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else set()
        self.progress_lock = Lock()
        self.file_progress = {}
        self.active_download_threads = []
        self.exit_flag = False

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
        self.file_list_display.place(relwidth=1, relheight=0.4)

        # Create and place input for file names
        self.file_entry_label = tk.Label(self, text="Enter file names to download (comma-separated) with optional priorities(CRITICAL, HIGH, NORMAL) :", bg='white', fg='black', font=('Times New Roman', 14))
        self.file_entry_label.place(rely=0.45, relwidth=1)

        self.file_entry = tk.Entry(self, bg='lavender', fg='black', font=('Times New Roman', 14))
        self.file_entry.place(relwidth=1, rely=0.52)

        # Create and place download button
        self.download_button = tk.Button(self, text="Download", command=self.download_files, bg='white', font=('Times New Roman', 16))
        self.download_button.place(relx=0.45, rely=0.58) 

        # Create and place progress display canvas
        self.progress_canvas = tk.Canvas(self, bg='white')
        self.progress_canvas.place(rely=0.65, relwidth=1, relheight=0.3)
        self.progress_bars = {}

    def get_file_list(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(ADDR)
                file_list_data = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
                self.available_files = file_list_data.split('\n')
                self.display_file_list()
        except socket.gaierror as e:
            messagebox.showerror("Connection Error", f"Failed to resolve hostname: {e}")
        except ConnectionRefusedError:
            messagebox.showerror("Connection Error", "Connection refused by the server.")
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
        file_inputs = self.file_entry.get().split(',')
        ongoing_downloads = set()
        self.file_progress = {}

        for file_input in file_inputs:
            try:
                parts = file_input.strip().split()
                file_name = parts[0]
                priority = parts[1].upper() if len(parts) > 1 else None

                if not any(file_name == file_info.split(':')[0] for file_info in self.available_files):
                    messagebox.showwarning("File Not Found", f"The file '{file_name}' is not available in the file list.")
                    continue

                if file_name in self.downloaded_files:
                    continue

                if file_name in ongoing_downloads:
                    messagebox.showinfo("Download Ongoing", f"The file '{file_name}' is already being downloaded.")
                    continue

                if file_name and (priority is None or priority in PRIORITY_VALUES):
                    with self.progress_lock:
                        self.file_progress[file_name] = 0
                        bar = tk.Label(self.progress_canvas, text=f"{file_name}: 0.00%", bg='gainsboro', fg='black', anchor='w')
                        bar.place(relwidth=1, relheight=0.1, rely=len(self.progress_bars) * 0.1)
                        self.progress_bars[file_name] = bar

                    priority_value = PRIORITY_VALUES.get(priority, None)
                    ongoing_downloads.add(file_name)
                    thread = Thread(target=self.download_file, args=(file_name, priority_value, ongoing_downloads))
                    thread.daemon = True
                    self.active_download_threads.append(thread)
                    thread.start()
            except ValueError:
                messagebox.showerror("Input Error", f"Invalid input format: '{file_input}'. Correct format: 'filename PRIORITY'.")

    def download_file(self, file_name, priority_value=None, ongoing_downloads=None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(ADDR)
                client_socket.sendall(file_name.encode(FORMAT))

                file_size_data = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
                file_size = int(file_size_data)

                with open(os.path.join(OUTPUT_DIR, file_name), 'wb') as f:
                    total_size = 0
                    buffer_size = BUFFER_SIZE * (priority_value if priority_value else 1)

                    while total_size < file_size:
                        data = client_socket.recv(buffer_size)

                        if not data:
                            break

                        f.write(data)
                        total_size += len(data)

                        self.update_progress(file_name, total_size)

                    self.update_progress(file_name, total_size, final=True)
                    self.downloaded_files.add(file_name)
                    ongoing_downloads.remove(file_name)  
                    messagebox.showinfo("Download Complete", f"The file '{file_name}' has been downloaded successfully.")

        except Exception as e:
            messagebox.showerror("Download Error", str(e))
            if ongoing_downloads:
                ongoing_downloads.remove(file_name)  

    def update_progress(self, file_name, downloaded_size, final=False):
        with self.progress_lock:
            if file_name in self.file_progress:
                total_size = int([f.split(':')[1] for f in self.available_files if f.startswith(file_name)][0])
                progress = (downloaded_size / total_size) * 100
                if final:
                    progress = 100.0  
                progress_text = f"{file_name}: {progress:.2f}%"
                bar = self.progress_bars[file_name]
                bar.config(text=progress_text)
                if final:
                    self.after(2000, bar.destroy)
                    del self.progress_bars[file_name]

    def on_exit(self, event=None):
        self.exit_flag = True
        self.after(100, self.check_for_exit)

    def handle_sigint(self, signal, frame):
        self.on_exit()

    def check_for_exit(self):
        if self.exit_flag:
            for thread in self.active_download_threads:
                thread.join(timeout=1)
            self.destroy()
        else:
            self.after(100, self.check_for_exit)

if __name__ == "__main__":
    app = FileDownloadClient()
    app.mainloop()
