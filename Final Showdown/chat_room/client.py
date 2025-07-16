# client.py
import socket
import threading

nickname = input("Choose a nickname: ")
if nickname == 'admin':
    password = input("Enter password for Admin: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 55579))

stop_thread = False

def receive():
    global stop_thread
    while True:
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            elif message == 'PASS':
                client.send(password.encode('ascii'))
            elif message == 'REFUSE':
                print("Connection was refused! Wrong password!")
                stop_thread = True
            elif message == 'BAN':
                print("You are banned from this server.")
                client.close()
                stop_thread = True
            else:
                print(message)
        except:
            print("An error occurred!")
            client.close()
            break

def write():
    global stop_thread
    while True:
        if stop_thread:
            break
        raw_msg = input("")
        message = f'{nickname}: {raw_msg}'
        if raw_msg.startswith('/'):
            if nickname == 'admin':
                if raw_msg.startswith('/kick'):
                    name_to_kick = raw_msg[6:]
                    client.send(f'KICK {name_to_kick}'.encode('ascii'))
                elif raw_msg.startswith('/ban'):
                    name_to_ban = raw_msg[5:]
                    client.send(f'BAN {name_to_ban}'.encode('ascii'))
            else:
                print("Commands can only be executed by the admin!")
        else:
            client.send(message.encode('ascii'))

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()
