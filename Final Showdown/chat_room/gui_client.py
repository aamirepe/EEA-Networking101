import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from tkinter import simpledialog

HOST = '127.0.0.1'
PORT = 22222

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# GUI Setup
class ChatClient:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Chat Room")
        self.win.configure(bg="#2c3e50")  # dark background
        self.win.grid_rowconfigure(1, weight=1)  # text_area row expands vertically
        self.win.grid_columnconfigure(0, weight=1)  # column 0 expands horizontally

        self.chat_label = tk.Label(self.win, text="Chat:", font=("Arial", 12))
        self.chat_label.configure(bg="#2c3e50", fg="white", font=("Helvetica", 14, "bold"))
        self.chat_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.text_area = scrolledtext.ScrolledText(self.win)
        self.text_area.config(state='disabled')
        self.text_area.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.msg_label = tk.Label(self.win, text="Message:", font=("Arial", 12))
        self.msg_label.configure(bg="#2c3e50", fg="white", font=("Helvetica", 14, "bold"))
        self.msg_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.input_area = tk.Text(self.win, height=3)
        self.input_area.grid(row=3, column=0, padx=10, pady=5)

        self.win.bind("<Return>", lambda event: self.write())
        self.input_area.focus_set()

        self.nickname = simpledialog.askstring("Nickname", "Please choose a nickname", parent=self.win)

        self.running = True

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()
        
        self.win.protocol("WM_DELETE_WINDOW", self.stop)
        self.win.mainloop()

    def write(self):
        message = f"{self.input_area.get('1.0', 'end').strip()}"
        client.send(message.encode('ascii'))
        self.input_area.delete('1.0', 'end')

    def stop(self):
        self.running = False
        client.close()
        self.win.destroy()

    def receive(self):
        while self.running:
            try:
                message = client.recv(1024).decode('ascii')
                if message == 'NICK':
                    client.send(self.nickname.encode('ascii'))
                else:
                    self.text_area.config(state='normal')
                    self.text_area.insert('end', message + "\n")
                    self.text_area.yview('end')
                    self.text_area.config(state='disabled')
            except:
                print("Error!")
                client.close()
                break

if __name__ == "__main__":
    ChatClient()

