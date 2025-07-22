# ServerWorker.py

import socket, threading, traceback
from random import randint

from VideoStream import VideoStream
from RtpPacket   import RtpPacket

class ServerWorker:
    # RTSP methods
    SETUP    = 'SETUP'
    PLAY     = 'PLAY'
    PAUSE    = 'PAUSE'
    TEARDOWN = 'TEARDOWN'

    # States
    INIT    = 0
    READY   = 1
    PLAYING = 2

    # Reply codes
    OK_200             = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500        = 2

    def __init__(self, clientInfo):
        self.clientInfo = clientInfo
        self.state      = ServerWorker.INIT
        self.sessionId  = randint(100000, 999999)

    def run(self):
        threading.Thread(target=self.recvRtspRequest).start()

    def recvRtspRequest(self):
        connSocket, clientAddr = self.clientInfo['rtspSocket']
        while True:
            try:
                data = connSocket.recv(1024)
                if not data:
                    break
                text = data.decode('utf-8')
                print("[Server] Received RTSP request:\n" + text)
                self.processRtspRequest(text, connSocket)
            except Exception:
                traceback.print_exc()
                break

    def processRtspRequest(self, data, connSocket):
        lines = data.replace('\r\n', '\n').split('\n')
        requestType, filename, _ = lines[0].split(' ')
        seq = int(lines[1].split(' ')[1])

        if requestType == ServerWorker.SETUP and self.state == ServerWorker.INIT:
            self.handleSetup(filename, seq, lines, connSocket)
        elif requestType == ServerWorker.PLAY and self.state == ServerWorker.READY:
            self.handlePlay(seq, connSocket)
        elif requestType == ServerWorker.PAUSE and self.state == ServerWorker.PLAYING:
            self.handlePause(seq, connSocket)
        elif requestType == ServerWorker.TEARDOWN:
            self.handleTeardown(seq, connSocket)

    def handleSetup(self, filename, seq, lines, connSocket):
        try:
            self.clientInfo['videoStream'] = VideoStream(filename)
            self.state = ServerWorker.READY
        except IOError:
            self.replyRtsp(ServerWorker.FILE_NOT_FOUND_404, seq, connSocket)
            return

        # Parse client RTP port from Transport header
        for line in lines:
            if line.startswith('Transport'):
                self.clientInfo['rtpPort'] = int(line.split('=')[-1])
                break

        # Create UDP socket for RTP
        self.clientInfo['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.replyRtsp(ServerWorker.OK_200, seq, connSocket)

    def handlePlay(self, seq, connSocket):
        self.state = ServerWorker.PLAYING
        self.clientInfo['event'] = threading.Event()
        threading.Thread(target=self.sendRtp).start()
        self.replyRtsp(ServerWorker.OK_200, seq, connSocket)

    def handlePause(self, seq, connSocket):
        self.state = ServerWorker.READY
        self.clientInfo['event'].set()
        self.replyRtsp(ServerWorker.OK_200, seq, connSocket)

    def handleTeardown(self, seq, connSocket):
        self.clientInfo.get('event', threading.Event()).set()
        self.replyRtsp(ServerWorker.OK_200, seq, connSocket)
        try:
            self.clientInfo['rtpSocket'].close()
        except:
            pass
        connSocket.close()

    def sendRtp(self):
        stream       = self.clientInfo['videoStream']
        rtpSocket    = self.clientInfo['rtpSocket']
        clientAddr,_ = self.clientInfo['rtspSocket'][1]
        clientPort   = self.clientInfo['rtpPort']
        event        = self.clientInfo['event']

        print(f"[Server] Starting RTP thread → sending to {clientAddr}:{clientPort}")

        while not event.isSet():
            data = stream.nextFrame()
            if not data:
                break
            frameNbr = stream.frameNbr()
            packet = RtpPacket()
            packet.encode(
                version   = 2, padding   = 0, extension=0, cc=0,
                seqnum    = frameNbr, marker=0,
                pt        = 26, ssrc=self.sessionId,
                payload   = data
            )
            try:
                rtpSocket.sendto(packet.getPacket(), (clientAddr, clientPort))
                print(f"[Server] Sent RTP packet for frame {frameNbr}")
            except Exception:
                break
            event.wait(1.0 / stream.fps)

    def replyRtsp(self, code, seq, connSocket):
        if code == ServerWorker.OK_200:
            reply = (
                "RTSP/1.0 200 OK\r\n"
                f"CSeq: {seq}\r\n"
                f"Session: {self.sessionId}\r\n\r\n"
            )
            connSocket.send(reply.encode('utf-8'))
            print(f"[Server] Sent 200 OK (CSeq={seq}, Session={self.sessionId})")
        elif code == ServerWorker.FILE_NOT_FOUND_404:
            reply = (
                "RTSP/1.0 404 NOT FOUND\r\n"
                f"CSeq: {seq}\r\n\r\n"
            )
            connSocket.send(reply.encode('utf-8'))
            print(f"[Server] Sent 404 NOT FOUND (CSeq={seq})")
        else:  # 500
            reply = (
                "RTSP/1.0 500 INTERNAL ERROR\r\n"
                f"CSeq: {seq}\r\n\r\n"
            )
            connSocket.send(reply.encode('utf-8'))
            print(f"[Server] Sent 500 INTERNAL ERROR (CSeq={seq})")
