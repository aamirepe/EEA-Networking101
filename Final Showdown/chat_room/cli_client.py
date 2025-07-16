import socket
import threading

nickname = input("Choose a nickname ")
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(("127.0.0.1",22222))

def receive():
    while True:
        try:
            msg = client.recv(1024).decode('ascii')
            if(msg == 'NICK'):
                client.send(f"{nickname}".encode('ascii'))
            else:
                print(msg)
        except:
            print("error occured")
            client.close()
            break
        
def write():
    while True:
        message = f'{nickname} : {input("")}'
        client.send(f'{message}'.encode('ascii'))

recv_thread = threading.Thread(target=receive)
recv_thread.start()
write_thread = threading.Thread(target=write)
write_thread.start()