import socket
import struct

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
MAX_PACKET_SIZE = 1500

class PSNChunkHeader:
    def __init__(self, raw_header):
        header = struct.unpack('<I', raw_header)[0]
        self.id = header & 0xFFFF
        self.data_len = (header >> 16) & 0x7FFF
        self.has_subchunks = (header >> 31) & 0x01

class PSNInfoPacketHeader:
    def __init__(self, data):
        self.timestamp, = struct.unpack('<Q', data[:8])
        self.version_high, = struct.unpack('<B', data[8:9])
        self.version_low, = struct.unpack('<B', data[9:10])
        self.frame_id, = struct.unpack('<B', data[10:11])
        self.frame_packet_count, = struct.unpack('<B', data[11:12])

class PSNDataPacketHeader:
    def __init__(self, data):
        self.timestamp, = struct.unpack('<Q', data[:8])
        self.version_high, = struct.unpack('<B', data[8:9])
        self.version_low, = struct.unpack('<B', data[9:10])
        self.frame_id, = struct.unpack('<B', data[10:11])
        self.frame_packet_count, = struct.unpack('<B', data[11:12])

# Define other chunk classes similarly...

def parse_chunks(data, offset=0):
    chunks = []
    while offset < len(data):
        chunk_header = PSNChunkHeader(data[offset:offset+4])
        offset += 4
        chunk_data = data[offset:offset + chunk_header.data_len]
        offset += chunk_header.data_len
        if chunk_header.id == 0x6756:
            chunks.append(('PSN_INFO_PACKET', parse_psn_info_packet(chunk_data)))
        elif chunk_header.id == 0x6755:
            chunks.append(('PSN_DATA_PACKET', parse_psn_data_packet(chunk_data)))
        # Add more conditions for other chunk types...
        else:
            chunks.append(('UNKNOWN_CHUNK', chunk_data))
    return chunks

def parse_psn_info_packet(data):
    chunks = []
    offset = 0
    while offset < len(data):
        chunk_header = PSNChunkHeader(data[offset:offset+4])
        offset += 4
        chunk_data = data[offset:offset + chunk_header.data_len]
        offset += chunk_header.data_len
        if chunk_header.id == 0x0000:
            chunks.append(('PSN_INFO_PACKET_HEADER', PSNInfoPacketHeader(chunk_data)))
        elif chunk_header.id == 0x0001:
            chunks.append(('PSN_INFO_SYSTEM_NAME', chunk_data.decode('utf-8')))
        # Add more conditions for other info chunk types...
        else:
            chunks.append(('UNKNOWN_CHUNK', chunk_data))
    return chunks

def parse_psn_data_packet(data):
    chunks = []
    offset = 0
    while offset < len(data):
        chunk_header = PSNChunkHeader(data[offset:offset+4])
        offset += 4
        chunk_data = data[offset:offset + chunk_header.data_len]
        offset += chunk_header.data_len
        if chunk_header.id == 0x0000:
            chunks.append(('PSN_DATA_PACKET_HEADER', PSNDataPacketHeader(chunk_data)))
        elif chunk_header.id == 0x0001:
            chunks.append(('PSN_DATA_TRACKER_LIST', chunk_data))
        # Add more conditions for other data chunk types...
        else:
            chunks.append(('UNKNOWN_CHUNK', chunk_data))
    return chunks

def start_udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, _ = sock.recvfrom(MAX_PACKET_SIZE)
        chunks = parse_chunks(data)
        # Process chunks as needed...
        print(chunks)

if __name__ == "__main__":
    start_udp_receiver()
