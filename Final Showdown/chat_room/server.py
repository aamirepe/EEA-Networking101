import threading
import socket


host = "127.0.0.1"  #local host 
port = 22222 #port number

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind((host,port))
server.listen()

clients =  []
nicknames = []

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            sender_index = clients.index(client)
            sender_nick = nicknames[sender_index]
            if message.startswith("/whisper"):
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    client.send("Usage: /whisper <nickname> <message>".encode('ascii'))
                    continue

                _, target_nick, private_msg = parts
                if target_nick in nicknames:
                    target_index = nicknames.index(target_nick)
                    target_client = clients[target_index]
                    target_client.send(f"[Private] {sender_nick} -> You: {private_msg}".encode('ascii'))
                    client.send(f"[Private] You -> {target_nick}: {private_msg}".encode('ascii'))
                else:
                    client.send(f"No user with nickname '{target_nick}' found.".encode('ascii'))
            else:
                broadcast(f'{sender_nick} : {message}'.encode('ascii'))
        except:
            index = clients.index(client)
            client.close()
            nickname = nicknames.pop(index)
            clients.pop(index)
            broadcast(f"{nickname} left the chat".encode('ascii'))
            break

def receive():
    while True:
        client,addr = server.accept()
        print(f"connected with {str(addr)}")
        client.send("NICK".encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        broadcast(f"{nickname} joined the chat".encode('ascii'))
        clients.append(client)
        nicknames.append(nickname)
        client.send('connected to chat server'.encode('ascii'))
        thread = threading.Thread(target=handle,args=(client,))
        thread.start()

print("Server is listening...")
receive()