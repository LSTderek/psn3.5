import socket
import struct

MCAST_GRP = '236.10.10.10'
MCAST_PORT = 56565
BUFFER_SIZE = 1500

def join_multicast_group(sock):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    group = socket.inet_aton(MCAST_GRP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def parse_chunk(data, offset):
    chunk_id, data_field = struct.unpack_from('<HI', data, offset)
    data_length = data_field & 0x0FFF
    has_subchunks = (data_field & 0x8000) != 0
    offset += struct.calcsize('<HI')
    chunk_data = data[offset:offset+data_length]
    offset += data_length
    return chunk_id, chunk_data, has_subchunks, offset

def parse_psn_info_packet(data):
    offset = 0
    
    while offset < len(data):
        chunk_id, chunk_data, has_subchunks, offset = parse_chunk(data, offset)
        
        print(f"Chunk ID: {chunk_id}, Data Length: {len(chunk_data)}, Has Subchunks: {has_subchunks}")
        
        if chunk_id == 0x6756:  # PSN_V2_INFO_PACKET
            print("PSN_V2_INFO_PACKET")
        elif chunk_id == 0x0000:  # PSN_INFO_PACKET_HEADER
            timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', chunk_data, 0)
            print(f"Timestamp: {timestamp}")
            print(f"Version: {version_high}.{version_low}")
            print(f"Frame ID: {frame_id}")
            print(f"Frame Packet Count: {frame_packet_count}")
        elif chunk_id == 0x0001:  # PSN_INFO_SYSTEM_NAME
            system_name = chunk_data.decode('utf-8').strip('\x00')
            print(f"System Name: {system_name}")
        elif chunk_id == 0x0002:  # PSN_INFO_TRACKER_LIST
            parse_tracker_list(chunk_data)

def parse_tracker_list(data):
    offset = 0
    while offset < len(data):
        tracker_id, tracker_chunk_data, tracker_has_subchunks, offset = parse_chunk(data, offset)
        print(f"Tracker ID: {tracker_id}, Data Length: {len(tracker_chunk_data)}, Has Subchunks: {tracker_has_subchunks}")
        if tracker_id == 0x0000:  # PSN_INFO_TRACKER_NAME
            tracker_name = tracker_chunk_data.decode('utf-8').strip('\x00')
            print(f"Tracker Name: {tracker_name}")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    join_multicast_group(sock)
    
    print(f"Listening for PSN packets on {MCAST_GRP}:{MCAST_PORT}...")
    
    try:
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            print("Packet received:")
            parse_psn_info_packet(data)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
