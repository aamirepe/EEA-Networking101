from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT  = ".jpg"

class Client:
    INIT    = 0
    READY   = 1
    PLAYING = 2
    state   = INIT

    SETUP    = 0
    PLAY     = 1
    PAUSE    = 2
    TEARDOWN = 3

    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master        = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()
        self.serverAddr    = serveraddr
        self.serverPort    = int(serverport)
        self.rtpPort       = int(rtpport)
        self.fileName      = filename
        self.rtspSeq       = 0
        self.sessionId     = 0
        self.requestSent   = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr      = 0

    def createWidgets(self):
        """Build GUI."""
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"]    = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)

        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"]    = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)

        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"]    = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)

        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"]    = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)

        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        try:
            os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
        except:
            pass

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def playMovie(self):
        """Play button handler."""
        if self.state == self.READY:
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    if currFrameNbr > self.frameNbr:  # Discard late packets
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                # Stop listening upon PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon TEARDOWN acknowledgement, close socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        with open(cachename, "wb") as file:
            file.write(data)
        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server via RTSP/TCP."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning(
                'Connection Failed',
                f"Cannot connect to {self.serverAddr}:{self.serverPort}"
            )

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        self.rtspSeq += 1

        if requestCode == self.SETUP and self.state == self.INIT:
            self.requestSent = self.SETUP
            request = (
                f"SETUP {self.fileName} RTSP/1.0\r\n"
                f"CSeq: {self.rtspSeq}\r\n"
                f"Transport: RTP/UDP;client_port={self.rtpPort}\r\n\r\n"
            )
            threading.Thread(target=self.recvRtspReply).start()

        elif requestCode == self.PLAY and self.state == self.READY:
            self.requestSent = self.PLAY
            request = (
                f"PLAY {self.fileName} RTSP/1.0\r\n"
                f"CSeq: {self.rtspSeq}\r\n"
                f"Session: {self.sessionId}\r\n\r\n"
            )

        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.requestSent = self.PAUSE
            request = (
                f"PAUSE {self.fileName} RTSP/1.0\r\n"
                f"CSeq: {self.rtspSeq}\r\n"
                f"Session: {self.sessionId}\r\n\r\n"
            )

        elif requestCode == self.TEARDOWN and self.state != self.INIT:
            self.requestSent = self.TEARDOWN
            request = (
                f"TEARDOWN {self.fileName} RTSP/1.0\r\n"
                f"CSeq: {self.rtspSeq}\r\n"
                f"Session: {self.sessionId}\r\n\r\n"
            )

        else:
            return

        self.rtspSocket.send(request.encode())
        print("\nData sent:\n" + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)
            if not reply:
                break
            self.parseRtspReply(reply.decode("utf-8"))

            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.strip().split("\r\n")
        seqNum = int(lines[1].split(" ")[1])
        if seqNum != self.rtspSeq:
            return

        session = int(lines[2].split(" ")[1])
        if self.sessionId == 0:
            self.sessionId = session
        elif session != self.sessionId:
            return

        status = int(lines[0].split(" ")[1])
        if status != 200:
            tkinter.messagebox.showwarning("RTSP Error", f"Server returned {status}")
            return

        if self.requestSent == self.SETUP:
            self.state = self.READY
            self.openRtpPort()

        elif self.requestSent == self.PLAY:
            self.state = self.PLAYING

        elif self.requestSent == self.PAUSE:
            self.state = self.READY
            self.playEvent.set()

        elif self.requestSent == self.TEARDOWN:
            self.state = self.INIT
            self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket bound to the client’s chosen port."""
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        try:
            self.rtpSocket.bind(("", self.rtpPort))
            print(f"[Client] Bound RTP socket on UDP port {self.rtpPort}")
        except Exception as e:
            tkinter.messagebox.showwarning(
                "Unable to Bind",
                f"Cannot bind UDP port {self.rtpPort}: {e}"
            )

    def handler(self):
        """Handler for window close."""
        self.pauseMovie()
        if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:
            self.playMovie()

if __name__ == "__main__":
    root = Tk()
    root.title("RTP Client")
    if len(sys.argv) != 5:
        print("Usage: ClientLauncher.py <Server_IP> <RTSP_Port> <RTP_Port> <Video_File>")
        sys.exit(1)
    app = Client(root, *sys.argv[1:])
    root.mainloop()
