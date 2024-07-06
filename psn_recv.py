import socket
import struct
import logging

# Multicast group and port
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Buffer size for UDP packet
BUFFER_SIZE = 1500

# Set up logging to output to a file
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("psn_data.log"),
        logging.StreamHandler()
    ]
)

def parse_psn_data_packet(data):
    """
    Parses a PSN_DATA packet and returns tracker positions.
    """
    try:
        packet_info = {}
        offset = 0

        # Extract header
        timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, offset)
        offset += struct.calcsize('<QBBBB')
        packet_info['timestamp'] = timestamp
        packet_info['version'] = f"{version_high}.{version_low}"
        packet_info['frame_id'] = frame_id
        packet_info['frame_packet_count'] = frame_packet_count

        # Loop through the packet chunks
        while offset < len(data):
            chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
            offset += struct.calcsize('<HH')

            if chunk_id == 0x0001:  # PSN_DATA_TRACKER_LIST
                end_offset = offset + chunk_length
                while offset < end_offset:
                    tracker_id, tracker_chunk_length = struct.unpack_from('<HH', data, offset)
                    offset += struct.calcsize('<HH')
                    tracker_data_offset = offset

                    tracker_info = {}
                    while offset < tracker_data_offset + tracker_chunk_length:
                        sub_chunk_id, sub_chunk_length = struct.unpack_from('<HH', data, offset)
                        offset += struct.calcsize('<HH')

                        if sub_chunk_id == 0x0000:  # PSN_DATA_TRACKER_POS
                            pos_x, pos_y, pos_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['position'] = (pos_x, pos_y, pos_z)
                            offset += struct.calcsize('<fff')
                        elif sub_chunk_id == 0x0000:  # PSN_DATA_TRACKER_NAME
                            tracker_name = struct.unpack_from(f'<{sub_chunk_length}s', data, offset)[0].decode('utf-8')
                            tracker_info['name'] = tracker_name
                            offset += struct.calcsize(f'<{sub_chunk_length}s')
                        else:
                            offset += sub_chunk_length

                    packet_info[f'tracker_{tracker_id}'] = tracker_info
            else:
                offset += chunk_length

        return packet_info
    except struct.error as e:
        logging.error(f"Error parsing packet: {e}")
        return {}

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))  # Bind to all interfaces

    # Join multicast group
    mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    logging.info("Listening for PSN data...")

    try:
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            logging.debug(f"Received data: {data}")
            packet_info = parse_psn_data_packet(data)
            
            for tracker_id, tracker_data in packet_info.items():
                if tracker_id.startswith('tracker_'):
                    tracker_id_num = tracker_id.split('_')[1]
                    position = tracker_data.get('position', None)
                    name = tracker_data.get('name', 'Unknown')
                    if position:
                        print(f'TrackerID: "{tracker_id_num}"')
                        print(f'TrackerName: "{name}"')
                        print(f'Pos: "{position[0]}, {position[1]}, {position[2]}"')

    except KeyboardInterrupt:
        logging.info("Exiting.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
