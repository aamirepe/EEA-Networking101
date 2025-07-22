# Server.py
import sys, socket
from ServerWorker import ServerWorker

class Server:
    def main(self):
        # Expect only the port on the command line
        if len(sys.argv) != 2:
            print("Usage: Server.py <Server_port>\n")
            sys.exit(1)

        SERVER_PORT = int(sys.argv[1])
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind(('', SERVER_PORT))
        rtspSocket.listen(5)

        print(f"[INFO] RTSP server listening on port {SERVER_PORT}")

        # Loop forever, handing each new TCP connection to a ServerWorker
        while True:
            clientConn, clientAddr = rtspSocket.accept()
            print(f"[INFO] Incoming connection from {clientAddr}")
            clientInfo = {
                'rtspSocket': (clientConn, clientAddr)
            }
            ServerWorker(clientInfo).run()

if __name__ == "__main__":
    Server().main()
