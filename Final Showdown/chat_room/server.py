import threading
import socket
import os

if not os.path.exists('bans.txt'):
    with open('bans.txt', 'w') as f:
        pass  

host = '127.0.0.1'
port = 55579

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def kick_user(name):
    if name in nicknames:
        index = nicknames.index(name)
        client_to_kick = clients[index]
        client_to_kick.send('You were kicked by the admin!'.encode('ascii'))
        client_to_kick.close()
        clients.remove(client_to_kick)
        nicknames.remove(name)
        broadcast(f'{name} was kicked by the admin!'.encode('ascii'))


def handle(client):
    while True:
        try:
            msg = message = client.recv(1024)
            if msg.decode('ascii').startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = msg.decode('ascii')[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command was refused!'.encode('ascii'))

            elif msg.decode('ascii').startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = msg.decode('ascii')[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt', 'a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned!')
                else:
                    client.send('Command was refused!'.encode('ascii'))

            else:
                broadcast(message)

        except:
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                broadcast(f'{nickname} left the chat!'.encode('ascii'))
                nicknames.remove(nickname)
                break

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        try:
            client.send('NICK'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')
        except:
            print("Client disconnected before sending nickname.")
            client.close()
            continue  # Skip to next connection

        with open('bans.txt', 'r') as f:
            bans = f.readlines()
        
        if nickname + '\n' in bans:
            client.send('BAN'.encode('ascii'))
            client.close()
            continue

        if nickname == 'admin':
            client.send('PASS'.encode('ascii'))
            try:
                password = client.recv(1024).decode('ascii')
            except:
                print("Admin disconnected before sending password.")
                client.close()
                continue

            if password != 'adminpass':
                client.send('REFUSE'.encode('ascii'))
                client.close()
                continue  # Skip to the next client

        nicknames.append(nickname)
        clients.append(client)

        print(f'Nickname of the client is {nickname}!')
        broadcast(f'{nickname} joined the chat!'.encode('ascii'))
        client.send('Connected to the server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server is listening...")
receive()
