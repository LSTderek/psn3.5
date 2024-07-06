import socket
import struct
import logging

# Multicast group and port
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Buffer size for UDP packet
BUFFER_SIZE = 1500

# Enable or disable debug logging
DEBUG_LOGGING = True

# Set up logging
if DEBUG_LOGGING:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("psn_data.log"),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("psn_data.log"),
            logging.StreamHandler()
        ]
    )

# Protocol and Chunk IDs
PSN_INFO_PACKET = 0x6756
PSN_DATA_PACKET = 0x6755
PSN_INFO_PACKET_HEADER = 0x0000
PSN_INFO_TRACKER_LIST = 0x0002
PSN_DATA_PACKET_HEADER = 0x0000
PSN_DATA_TRACKER_LIST = 0x0001
PSN_DATA_TRACKER_POS = 0x0000

tracker_names = {}
tracker_count = 0

class PSNDecoder:
    def __init__(self):
        self.tracker_names = {}
        self.packet_info = {}

    def decode_info_packet(self, data):
        offset = 0

        # Extract and log the header
        chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
        offset += struct.calcsize('<HH')
        logging.debug(f"PSN_INFO_PACKET_HEADER - Chunk ID: {chunk_id}, Length: {chunk_length}")

        if chunk_id == PSN_INFO_PACKET_HEADER:
            timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, offset)
            offset += struct.calcsize('<QBBBB')
            logging.debug(f"PSN_INFO_PACKET_HEADER - Timestamp: {timestamp}, Version: {version_high}.{version_low}, Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Loop through the packet chunks
        while offset < len(data):
            chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
            offset += struct.calcsize('<HH')
            logging.debug(f"PSN_INFO Chunk - ID: {chunk_id}, Length: {chunk_length}")

            if chunk_id == PSN_INFO_TRACKER_LIST:
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

                    self.tracker_names[tracker_id] = tracker_info['name']
                    logging.debug(f"Tracker ID: {tracker_id}, Name: {tracker_info.get('name', 'Unknown')}")
            else:
                offset += chunk_length

    def decode_data_packet(self, data):
        offset = 0

        # Extract and log the header
        chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
        offset += struct.calcsize('<HH')
        logging.debug(f"PSN_DATA_PACKET_HEADER - Chunk ID: {chunk_id}, Length: {chunk_length}")

        if chunk_id == PSN_DATA_PACKET_HEADER:
            timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<QBBBB', data, offset)
            offset += struct.calcsize('<QBBBB')
            logging.debug(f"PSN_DATA_PACKET_HEADER - Timestamp: {timestamp}, Version: {version_high}.{version_low}, Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Loop through the packet chunks
        while offset < len(data):
            chunk_id, chunk_length = struct.unpack_from('<HH', data, offset)
            offset += struct.calcsize('<HH')
            logging.debug(f"PSN_DATA Chunk - ID: {chunk_id}, Length: {chunk_length}")

            if chunk_id == PSN_DATA_TRACKER_LIST:
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

                        if sub_chunk_length == 32856:
                            logging.debug("Found large sub-chunk indicating new tracker data")
                            tracker_id, tracker_chunk_length = struct.unpack_from('<HH', data, offset)
                            offset += struct.calcsize('<HH')
                            tracker_data_offset = offset
                            logging.debug(f"PSN_DATA Tracker - ID: {tracker_id}, Chunk Length: {tracker_chunk_length}")

                        if sub_chunk_id == PSN_DATA_TRACKER_POS:
                            pos_x, pos_y, pos_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['position'] = (pos_x, pos_y, pos_z)
                            offset += struct.calcsize('<fff')
                        else:
                            offset += sub_chunk_length

                    if tracker_id in self.packet_info:
                        logging.debug(f"Duplicate Tracker ID found: {tracker_id}, overwriting previous data")
                    self.packet_info[tracker_id] = tracker_info
                    logging.debug(f"Tracker ID: {tracker_id}, Position: {tracker_info.get('position', 'Unknown')}")
            else:
                offset += chunk_length

    def get_tracker_info(self):
        for tracker_id, tracker_data in self.packet_info.items():
            if tracker_id in self.tracker_names:
                name = self.tracker_names[tracker_id]
                position = tracker_data.get('position', None)
                if position:
                    print(f'TrackerID: "{tracker_id}"')
                    print(f'TrackerName: "{name}"')
                    print(f'Pos: "{position[0]}, {position[1]}, {position[2]}"')

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))  # Bind to all interfaces

    # Join multicast group
    mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    logging.info("Listening for PSN data...")

    decoder = PSNDecoder()

    try:
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            logging.debug(f"Raw data received: {data.hex()}")
            if len(data) > 4:
                header_id = struct.unpack_from('<H', data, 0)[0]
                if header_id == PSN_INFO_PACKET:
                    logging.debug("Received PSN_INFO packet")
                    decoder.decode_info_packet(data)
                elif header_id == PSN_DATA_PACKET:
                    logging.debug("Received PSN_DATA packet")
                    decoder.decode_data_packet(data)
                    decoder.get_tracker_info()

    except KeyboardInterrupt:
        logging.info("Exiting.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
