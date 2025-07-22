import sys
from time import time
HEADER_SIZE = 12

class RtpPacket:
    header = bytearray(HEADER_SIZE)

    def __init__(self):
        self.header = bytearray(HEADER_SIZE)
        self.payload = b''

    def encode(self, version, padding, extension, cc,
               seqnum, marker, pt, ssrc, payload):
        """Encode the RTP packet with header fields and payload."""
        # 1) First byte: V(2 bits), P(1), X(1), CC(4)
        self.header[0] = ((version & 0x03) << 6) | \
                         ((padding & 0x01) << 5) | \
                         ((extension & 0x01) << 4) | \
                         (cc & 0x0F)

        # 2) Second byte: M(1), PT(7)
        self.header[1] = ((marker & 0x01) << 7) | (pt & 0x7F)

        # 3) Sequence number: 16 bits
        self.header[2] = (seqnum >> 8) & 0xFF
        self.header[3] = seqnum & 0xFF

        # 4) Timestamp: 32 bits (using current time as an integer)
        timestamp = int(time())
        self.header[4] = (timestamp >> 24) & 0xFF
        self.header[5] = (timestamp >> 16) & 0xFF
        self.header[6] = (timestamp >> 8) & 0xFF
        self.header[7] = timestamp & 0xFF

        # 5) SSRC: 32 bits
        self.header[8]  = (ssrc >> 24) & 0xFF
        self.header[9]  = (ssrc >> 16) & 0xFF
        self.header[10] = (ssrc >> 8) & 0xFF
        self.header[11] = ssrc & 0xFF

        # 6) Store payload
        self.payload = payload

    def decode(self, byteStream):
        """Decode the RTP packet."""
        self.header = bytearray(byteStream[:HEADER_SIZE])
        self.payload = byteStream[HEADER_SIZE:]

    def version(self):
        """Return RTP version."""
        return int(self.header[0] >> 6)

    def seqNum(self):
        """Return sequence (frame) number."""
        return int((self.header[2] << 8) | self.header[3])

    def timestamp(self):
        """Return timestamp."""
        return int(
            (self.header[4] << 24) |
            (self.header[5] << 16) |
            (self.header[6] << 8) |
             self.header[7]
        )

    def payloadType(self):
        """Return payload type."""
        return int(self.header[1] & 0x7F)

    def getPayload(self):
        """Return payload."""
        return self.payload

    def getPacket(self):
        """Return RTP packet (header + payload)."""
        return bytes(self.header) + self.payload
