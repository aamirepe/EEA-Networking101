import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import subprocess
import os
import sys

def start_server_gui():
    def run_server():
        import server
        server.start_server()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    messagebox.showinfo("Server", "Server started. Others can now join.")
    launch_client()

def launch_client():
    script_dir = os.path.dirname(os.path.abspath(__file__))  # path of chat_entry.py
    gui_client_path = os.path.join(script_dir, "gui_client.py")
    print(f"Launching client at {gui_client_path}")
    subprocess.Popen([sys.executable, gui_client_path])


def show_menu():
    root = tk.Tk()
    root.title("Chat Room Entry")
    root.geometry("300x200")

    label = tk.Label(root, text="Choose an option", font=("Arial", 14))
    label.pack(pady=20)

    host_button = tk.Button(root, text="Start a Chat Room", command=start_server_gui, font=("Arial", 12))
    host_button.pack(pady=10)

    join_button = tk.Button(root, text="Join a Chat Room", command=launch_client, font=("Arial", 12))
    join_button.pack(pady=10)

    root.mainloop()

show_menu()
