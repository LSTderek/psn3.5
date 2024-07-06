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
PSN_DATA_PACKET = 0x6755
PSN_DATA_PACKET_HEADER = 0x0000
PSN_DATA_TRACKER_LIST = 0x0001
PSN_DATA_TRACKER_POS = 0x0000
PSN_DATA_TRACKER_SPEED = 0x0001
PSN_DATA_TRACKER_ORI = 0x0002
PSN_DATA_TRACKER_STATUS = 0x0003
PSN_DATA_TRACKER_ACCEL = 0x0004
PSN_DATA_TRACKER_TRGTPOS = 0x0005

class PSNDecoder:
    def __init__(self):
        self.packet_info = {}

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
                        if offset + struct.calcsize('<HH') > len(data):
                            logging.warning(f"Not enough buffer left to unpack sub-chunk ID and length at offset {offset}")
                            break

                        sub_chunk_id, sub_chunk_length = struct.unpack_from('<HH', data, offset)
                        offset += struct.calcsize('<HH')
                        logging.debug(f"PSN_DATA Tracker Sub-Chunk - ID: {sub_chunk_id}, Length: {sub_chunk_length}")

                        # Check if buffer size is sufficient before unpacking
                        remaining_buffer_size = len(data) - offset
                        logging.debug(f"Remaining Buffer Size: {remaining_buffer_size}, Sub-Chunk Length: {sub_chunk_length}")

                        if remaining_buffer_size < sub_chunk_length:
                            logging.warning(f"Buffer too small for sub-chunk. Expected: {sub_chunk_length}, Remaining: {remaining_buffer_size}")
                            break

                        if sub_chunk_id == PSN_DATA_TRACKER_POS and remaining_buffer_size >= struct.calcsize('<fff'):
                            pos_x, pos_y, pos_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['pos_x'] = pos_x
                            tracker_info['pos_y'] = pos_y
                            tracker_info['pos_z'] = pos_z
                            offset += struct.calcsize('<fff')
                        elif sub_chunk_id == PSN_DATA_TRACKER_SPEED and remaining_buffer_size >= struct.calcsize('<fff'):
                            speed_x, speed_y, speed_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['spd_x'] = speed_x
                            tracker_info['spd_y'] = speed_y
                            tracker_info['spd_z'] = speed_z
                            offset += struct.calcsize('<fff')
                        elif sub_chunk_id == PSN_DATA_TRACKER_ORI and remaining_buffer_size >= struct.calcsize('<fff'):
                            ori_x, ori_y, ori_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['ori_x'] = ori_x
                            tracker_info['ori_y'] = ori_y
                            tracker_info['ori_z'] = ori_z
                            offset += struct.calcsize('<fff')
                        elif sub_chunk_id == PSN_DATA_TRACKER_STATUS and remaining_buffer_size >= struct.calcsize('<I'):
                            status = struct.unpack_from('<I', data, offset)[0]
                            tracker_info['status'] = status
                            offset += struct.calcsize('<I')
                        elif sub_chunk_id == PSN_DATA_TRACKER_ACCEL and remaining_buffer_size >= struct.calcsize('<fff'):
                            accel_x, accel_y, accel_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['accel_x'] = accel_x
                            tracker_info['accel_y'] = accel_y
                            tracker_info['accel_z'] = accel_z
                            offset += struct.calcsize('<fff')
                        elif sub_chunk_id == PSN_DATA_TRACKER_TRGTPOS and remaining_buffer_size >= struct.calcsize('<fff'):
                            trgtpos_x, trgtpos_y, trgtpos_z = struct.unpack_from('<fff', data, offset)
                            tracker_info['trgtpos_x'] = trgtpos_x
                            tracker_info['trgtpos_y'] = trgtpos_y
                            tracker_info['trgtpos_z'] = trgtpos_z
                            offset += struct.calcsize('<fff')
                        else:
                            offset += sub_chunk_length

                    if tracker_id in self.packet_info:
                        logging.debug(f"Duplicate Tracker ID found: {tracker_id}, overwriting previous data")
                    self.packet_info[tracker_id] = tracker_info
                    logging.debug(f"Tracker ID: {tracker_id}, Data: {tracker_info}")
            else:
                offset += chunk_length

    def get_tracker_info(self):
        for tracker_id, tracker_data in self.packet_info.items():
            print(f'TrackerID: "{tracker_id}"')
            for key, value in tracker_data.items():
                print(f'{key}: {value}')

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
                if header_id == PSN_DATA_PACKET:
                    logging.debug("Received PSN_DATA packet")
                    decoder.decode_data_packet(data)
                    decoder.get_tracker_info()

    except KeyboardInterrupt:
        logging.info("Exiting.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
