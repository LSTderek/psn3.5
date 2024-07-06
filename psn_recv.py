import socket
import struct

# Constants for PosiStageNet
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Function to parse and display PSN_INFO packets
def parse_psn_info_packet(data, depth=0):
    index = 0
    tracker_count = 0
    trackers = []

    while index < len(data):
        chunk_id, data_field = struct.unpack_from('<HH', data, index)
        data_len = data_field & 0x7FFF
        has_subchunks = (data_field >> 15) & 0x1
        index += 4

        indent = '    ' * depth
        print(f"{indent}Chunk ID: {chunk_id:#06x}")
        print(f"{indent}Data Length: {data_len}")
        print(f"{indent}Has Sub Chunks: {'Yes' if has_subchunks else 'No'}")

        if chunk_id == 0x6756:  # PSN_INFO_PACKET
            trackers = parse_psn_info_packet(data[index:index + data_len], depth + 1)
            tracker_count = len(trackers)
        elif chunk_id == 0x0000:  # PSN_INFO_PACKET_HEADER
            timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, index)
            print(f"{indent}Timestamp: {timestamp}")
            print(f"{indent}Version High: {version_high}")
            print(f"{indent}Version Low: {version_low}")
            print(f"{indent}Frame ID: {frame_id}")
            print(f"{indent}Frame Packet Count: {frame_packet_count}")
        elif chunk_id == 0x0001:  # PSN_INFO_SYSTEM_NAME
            system_name = data[index:index + data_len].decode('utf-8')
            print(f"{indent}System Name: {system_name}")
        elif chunk_id == 0x0002:  # PSN_INFO_TRACKER_LIST
            trackers = parse_tracker_list(data[index:index + data_len], depth + 1)
            tracker_count = len(trackers)

        index += data_len

    if depth == 0:
        print(f"Number of Trackers: {tracker_count}")
        for tracker in trackers:
            print(f"Tracker ID: {tracker['id']}, Name: {tracker['name']}")

    return trackers

# Function to parse tracker list
def parse_tracker_list(data, depth=0):
    index = 0
    trackers = []

    while index < len(data):
        tracker_id, data_field = struct.unpack_from('<HH', data, index)
        data_len = data_field & 0x7FFF
        has_subchunks = (data_field >> 15) & 0x1
        index += 4

        indent = '    ' * depth
        print(f"{indent}Tracker ID: {tracker_id}")
        print(f"{indent}Data Length: {data_len}")
        print(f"{indent}Has Sub Chunks: {'Yes' if has_subchunks else 'No'}")

        tracker_name = ''
        if has_subchunks:
            subchunk_id, subchunk_field = struct.unpack_from('<HH', data, index)
            subchunk_len = subchunk_field & 0x7FFF
            subchunk_has_subchunks = (subchunk_field >> 15) & 0x1
            index += 4

            if subchunk_id == 0x0000:  # PSN_INFO_TRACKER_NAME
                tracker_name = data[index:index + subchunk_len].decode('utf-8')
                print(f"{indent}Tracker Name: {tracker_name}")
                index += subchunk_len

        trackers.append({'id': tracker_id, 'name': tracker_name})
        index += data_len

    return trackers

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
