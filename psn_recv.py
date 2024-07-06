import socket
import struct

# Constants
MULTICAST_IP = "236.10.10.10"
PORT = 56565

# Define data structures
class PSNChunkHeader:
    def __init__(self, id, data_len, has_subchunks):
        self.id = id
        self.data_len = data_len
        self.has_subchunks = has_subchunks

class PSNInfoPacket:
    def __init__(self, header, timestamp, version_high, version_low, frame_id, frame_packet_count):
        self.header = header
        self.timestamp = timestamp
        self.version_high = version_high
        self.version_low = version_low
        self.frame_id = frame_id
        self.frame_packet_count = frame_packet_count

class PSNDataPacket:
    def __init__(self, header, timestamp, version_high, version_low, frame_id, frame_packet_count):
        self.header = header
        self.timestamp = timestamp
        self.version_high = version_high
        self.version_low = version_low
        self.frame_id = frame_id
        self.frame_packet_count = frame_packet_count

# Initialize UDP multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((MULTICAST_IP, PORT))
mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_IP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def parse_packet(data):
    print(f"Raw data: {data.hex()}")  # Debugging: print raw packet data in hexadecimal

    # Ensure packet is long enough to include header
    if len(data) < 8:
        print("Packet too short for header")
        return None

    # Parse chunk header
    chunk_id, data_len, has_subchunks = struct.unpack("<IHH", data[:8])
    header = PSNChunkHeader(chunk_id, data_len, has_subchunks)
    
    print(f"Chunk ID: {hex(chunk_id)}, Data Length: {data_len}, Has Subchunks: {has_subchunks}")  # Debugging: print header details

    # Check known packet types
    if chunk_id == 0x5567cc80:  # Assuming this is a correct packet type from observed data
        if len(data) < 20:
            print("Packet too short for PSN_INFO_PACKET or PSN_DATA_PACKET")
            return None

        timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack("<QBBBB", data[8:20])
        print(f"Timestamp: {timestamp}, Version High: {version_high}, Version Low: {version_low}, Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Further classify as PSN_INFO_PACKET or PSN_DATA_PACKET based on additional checks if necessary
        if some_condition:  # Replace with appropriate condition
            packet = PSNInfoPacket(header, timestamp, version_high, version_low, frame_id, frame_packet_count)
            print(f"PSN_INFO_PACKET received: {packet.__dict__}")
        else:
            packet = PSNDataPacket(header, timestamp, version_high, version_low, frame_id, frame_packet_count)
            print(f"PSN_DATA_PACKET received: {packet.__dict__}")
    else:
        print(f"Unknown packet type: {hex(chunk_id)}")
        packet = None

    return packet

# Main loop to receive and process packets
while True:
    data, _ = sock.recvfrom(1500)
    packet = parse_packet(data)
    # Further processing of the packet, logging or printing the data
