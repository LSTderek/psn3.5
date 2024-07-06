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

    def __str__(self):
        return f"Chunk ID: {self.id}, Data Length: {self.data_len}, Has Subchunks: {self.has_subchunks}"

class PSNInfoPacketHeader:
    def __init__(self, data):
        self.timestamp, = struct.unpack('<Q', data[:8])
        self.version_high, = struct.unpack('<B', data[8:9])
        self.version_low, = struct.unpack('<B', data[9:10])
        self.frame_id, = struct.unpack('<B', data[10:11])
        self.frame_packet_count, = struct.unpack('<B', data[11:12])

    def __str__(self):
        return (f"Timestamp: {self.timestamp}, Version High: {self.version_high}, "
                f"Version Low: {self.version_low}, Frame ID: {self.frame_id}, "
                f"Frame Packet Count: {self.frame_packet_count}")

def parse_chunks(data, offset=0):
    chunks = []
    while offset < len(data):
        chunk_header = PSNChunkHeader(data[offset:offset+4])
        offset += 4
        chunk_data = data[offset:offset + chunk_header.data_len]
        offset += chunk_header.data_len
        if chunk_header.id == 0x6756:
            chunks.append(('PSN_INFO_PACKET', parse_psn_info_packet(chunk_data)))
        # Ignore other chunk types for now...
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
        elif chunk_header.id == 0x0002:
            chunks.append(('PSN_INFO_TRACKER_LIST', parse_psn_info_tracker_list(chunk_data)))
        # Add more conditions for other info chunk types...
        else:
            chunks.append(('UNKNOWN_CHUNK', chunk_data))
    return chunks

def parse_psn_info_tracker_list(data):
    chunks = []
    offset = 0
    while offset < len(data):
        chunk_header = PSNChunkHeader(data[offset:offset+4])
        offset += 4
        chunk_data = data[offset:offset + chunk_header.data_len]
        offset += chunk_header.data_len
        tracker_id = chunk_header.id
        tracker_name = chunk_data.decode('utf-8').strip()
        chunks.append((tracker_id, tracker_name))
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
        for chunk_type, chunk_data in chunks:
            if chunk_type == 'PSN_INFO_PACKET':
                print("PSN_INFO_PACKET:")
                for sub_chunk_type, sub_chunk_data in chunk_data:
                    if sub_chunk_type == 'PSN_INFO_PACKET_HEADER':
                        print(f"  {sub_chunk_type}: {sub_chunk_data}")
                    elif sub_chunk_type == 'PSN_INFO_SYSTEM_NAME':
                        print(f"  PSN_INFO_SYSTEM_NAME: {sub_chunk_data}")
                    elif sub_chunk_type == 'PSN_INFO_TRACKER_LIST':
                        print("  PSN_INFO_TRACKER_LIST:")
                        for tracker_id, tracker_name in sub_chunk_data:
                            print(f"    TrackerID: {tracker_id:<5} Name: {tracker_name}")
                    else:
                        print(f"  {sub_chunk_type}: {sub_chunk_data}")

if __name__ == "__main__":
    start_udp_receiver()
