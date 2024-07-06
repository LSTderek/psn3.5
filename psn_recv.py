import socket
import struct

# Multicast group details
MCAST_GRP = '236.10.10.10'
MCAST_PORT = 56565

# Buffer size for receiving data
BUFFER_SIZE = 1500

def join_multicast_group(sock):
    # Allow multiple sockets to use the same PORT number
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the port
    sock.bind(('', MCAST_PORT))
    
    # Request the kernel to join the multicast group
    group = socket.inet_aton(MCAST_GRP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def parse_psn_info_packet(data):
    offset = 0
    
    # PSN_INFO_PACKET_HEADER
    (timestamp, version_high, version_low, frame_id, frame_packet_count) = struct.unpack_from('<QBBBB', data, offset)
    offset += struct.calcsize('<QBBBB')
    
    print(f"Timestamp: {timestamp}")
    print(f"Version: {version_high}.{version_low}")
    print(f"Frame ID: {frame_id}")
    print(f"Frame Packet Count: {frame_packet_count}")
    
    while offset < len(data):
        chunk_id, chunk_len = struct.unpack_from('<HI', data, offset)
        offset += struct.calcsize('<HI')
        
        if chunk_id == 0x0001:  # PSN_INFO_SYSTEM_NAME
            system_name = struct.unpack_from(f'{chunk_len}s', data, offset)[0].decode('utf-8')
            print(f"System Name: {system_name}")
        elif chunk_id == 0x0002:  # PSN_INFO_TRACKER_LIST
            end = offset + chunk_len
            while offset < end:
                tracker_id, tracker_len = struct.unpack_from('<HI', data, offset)
                offset += struct.calcsize('<HI')
                
                if tracker_id == 0x0000:  # PSN_INFO_TRACKER_NAME
                    tracker_name = struct.unpack_from(f'{tracker_len}s', data, offset)[0].decode('utf-8')
                    print(f"Tracker Name: {tracker_name}")
                offset += tracker_len
        offset += chunk_len

def main():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # Join the multicast group
    join_multicast_group(sock)
    
    print(f"Listening for PSN packets on {MCAST_GRP}:{MCAST_PORT}...")
    
    try:
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            parse_psn_info_packet(data)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        sock.close()

if __name__ == '__main__':
    main()
