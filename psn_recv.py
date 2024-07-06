import socket
import struct

# Constants for PosiStageNet
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Define function to parse and display PSN_INFO packets
def parse_psn_info_packet(data):
    index = 0
    while index < len(data):
        chunk_id, data_len, has_subchunks = struct.unpack_from('<HHH', data, index)
        index += 6
        has_subchunks = (has_subchunks >> 15) & 0x1
        print(f"Chunk ID: {chunk_id:#06x}")
        print(f"Data Length: {data_len}")
        print(f"Has Sub Chunks: {'Yes' if has_subchunks else 'No'}")
        if chunk_id == 0x6756:  # PSN_INFO_PACKET
            parse_psn_info_packet(data[index:index+data_len])
        elif chunk_id == 0x0000:  # PSN_INFO_PACKET_HEADER
            timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, index)
            print(f"Timestamp: {timestamp}")
            print(f"Version High: {version_high}")
            print(f"Version Low: {version_low}")
            print(f"Frame ID: {frame_id}")
            print(f"Frame Packet Count: {frame_packet_count}")
        elif chunk_id == 0x0001:  # PSN_INFO_SYSTEM_NAME
            system_name = data[index:index+data_len].decode('utf-8')
            print(f"System Name: {system_name}")
        elif chunk_id == 0x0002:  # PSN_INFO_TRACKER_LIST
            parse_psn_info_packet(data[index:index+data_len])
        index += data_len

# Set up UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.bind((MULTICAST_GROUP, PORT))
mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

print("Listening for PosiStageNet packets...")

while True:
    data, addr = sock.recvfrom(1500)
    print(f"Received packet from {addr}")
    parse_psn_info_packet(data)
