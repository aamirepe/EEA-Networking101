import sys
from tkinter import Tk
from Client import Client

if __name__ == "__main__":
    # Check command‑line args
    if len(sys.argv) != 5:
        print("Usage: ClientLauncher.py <Server_IP> <RTSP_Port> <RTP_Port> <Video_File>")
        sys.exit(1)

    serverAddr = sys.argv[1]
    serverPort = sys.argv[2]
    rtpPort    = sys.argv[3]
    fileName   = sys.argv[4]

    # Start the Tkinter GUI and Client
    root = Tk()
    root.title("RTP Client")
    app = Client(root, serverAddr, serverPort, rtpPort, fileName)
    root.mainloop()
