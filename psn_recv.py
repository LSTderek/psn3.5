import socket
import struct
import logging

# Multicast group and port
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Buffer size for UDP packet
BUFFER_SIZE = 1500

# Set up logging to output to a file and console
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("psn_data.log"),
        logging.StreamHandler()
    ]
)

def parse_psn_info_packet(data):
    """
    Parses a PSN_INFO packet and returns tracker names.
    """
    packet_info = {}
    offset = 0

    try:
        # Extract header
        timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, offset)
        offset += struct.calcsize('<QBBBB')
        logging.debug(f"PSN_INFO Header - Timestamp: {timestamp}, Version: {version_high}.{version_low}, Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Loop through the packet chunks
        while offset < len(data):
            chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
            offset += struct.calcsize('<HH')
            logging.debug(f"PSN_INFO Chunk - ID: {chunk_id}, Length: {chunk_length}")

            if chunk_id == 0x0002:  # PSN_INFO_TRACKER_LIST
                end_offset = offset + chunk_length
                while offset < end_offset:
                    tracker_id, tracker_chunk_length = struct.unpack_from('<HH', data, offset)
                    offset += struct.calcsize('<HH')
                    tracker_data_offset = offset
                    logging.debug(f"PSN_INFO Tracker - ID: {tracker_id}, Chunk Length: {tracker_chunk_length}")

                    tracker_info = {}
                    while offset < tracker_data_offset + tracker_chunk_length:
                        sub_chunk_id, sub_chunk_length = struct.unpack_from('<HH', data, offset)
                        offset += struct.calcsize('<HH')
                        logging.debug(f"PSN_INFO Tracker Sub-Chunk - ID: {sub_chunk_id}, Length: {sub_chunk_length}")

                        if sub_chunk_id == 0x0000:  # PSN_INFO_TRACKER_NAME
                            tracker_name = struct.unpack_from(f'<{sub_chunk_length}s', data, offset)[0].decode('utf-8').strip('\x00')
                            tracker_info['name'] = tracker_name
                            offset += sub_chunk_length
                        else:
                            offset += sub_chunk_length

                    packet_info[f'tracker_{tracker_id}'] = tracker_info
                    logging.debug(f"Tracker ID: {tracker_id}, Name: {tracker_info.get('name', 'Unknown')}")
            else:
                offset += chunk_length

    except struct.error as e:
        logging.error(f"Error parsing PSN_INFO packet: {e}")

    return packet_info

def parse_psn_data_packet(data):
    """
    Parses a PSN_DATA packet and returns tracker positions.
    """
    packet_info = {}
    offset = 0

    try:
        # Extract header
        timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, offset)
        offset += struct.calcsize('<QBBBB')
        logging.debug(f"PSN_DATA Header - Timestamp: {timestamp}, Version: {version_high}.{version_low}, Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Loop through the packet chunks
        while offset < len(data):
            chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
            offset += struct.calcsize('<HH')
            logging.debug(f"PSN_DATA Chunk - ID: {chunk_id}, Length: {chunk_length}")

            if chunk_id == 0x0001:  # PSN_DATA_TRACKER_LIST
                end_offset = offset + chunk_length
                while offset < end_offset:
                    tracker_id, tracker_chunk_length = struct.unpack_from('<HH', data, offset)
                    offset += struct.calcsize('<HH')
                    tracker_data_offset = offset
                    logging.debug(f"PSN_DATA Tracker - ID: {tracker_id}, Chunk Length: {tracker_chunk_length}")

                    tracker_info = {}
                    while offset < tracker_data_offset + tracker_chunk_length:
                        sub_chunk_id, sub_chunk_length = struct.unpack_from('<HH', data, offset)
                        offset += struct.calcsize('<HH')
                        logging.debug(f"PSN_DATA Tracker Sub-Chunk - ID: {sub_chunk_id}, Length: {sub_chunk_length}")

                        if sub_chunk_id == 0x0000:  # PSN_DATA_TRACKER_POS
                            pos_x, pos_y, pos_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['position'] = (pos_x, pos_y, pos_z)
                            offset += struct.calcsize('<fff')
                        else:
                            offset += sub_chunk_length

                    packet_info[f'tracker_{tracker_id}'] = tracker_info
                    logging.debug(f"Tracker ID: {tracker_id}, Position: {tracker_info.get('position', 'Unknown')}")
            else:
                offset += chunk_length

    except struct.error as e:
        logging.error(f"Error parsing PSN_DATA packet: {e}")

    return packet_info

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))  # Bind to all interfaces

    # Join multicast group
    mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    logging.info("Listening for PSN data...")

    tracker_names = {}

    try:
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            if len(data) > 4:
                header_id = struct.unpack_from('<H', data, 0)[0]
                if header_id == 0x6756:  # PSN_INFO_PACKET
                    logging.debug("Received PSN_INFO packet")
                    tracker_names.update(parse_psn_info_packet(data))
                elif header_id == 0x6755:  # PSN_DATA_PACKET
                    logging.debug("Received PSN_DATA packet")
                    packet_info = parse_psn_data_packet(data)
                    
                    for tracker_id, tracker_data in packet_info.items():
                        if tracker_id.startswith('tracker_'):
                            tracker_id_num = tracker_id.split('_')[1]
                            position = tracker_data.get('position', None)
                            name = tracker_names.get(f'tracker_{tracker_id_num}', {}).get('name', 'Unknown')
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
