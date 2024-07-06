import socket
import struct
import logging
from logging.handlers import RotatingFileHandler

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
MAX_PACKET_SIZE = 1500

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = False
LOG_FILE = 'psn_receiver.log'

# Set up logging
logger = logging.getLogger('PSNReceiver')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if LOG_TO_FILE:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

if LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class PSNChunkHeader:
    def __init__(self, raw_header):
        try:
            header = struct.unpack('<I', raw_header)[0]
            self.id = header & 0xFFFF
            self.data_len = (header >> 16) & 0x7FFF
            self.has_subchunks = (header >> 31) & 0x01
        except struct.error as e:
            logger.error(f"Failed to unpack PSNChunkHeader: {e}")
            self.id = 0
            self.data_len = 0
            self.has_subchunks = 0

    def __str__(self):
        return f"Chunk ID: {self.id}, Data Length: {self.data_len}, Has Subchunks: {self.has_subchunks}"

class PSNInfoPacketHeader:
    def __init__(self, data):
        try:
            self.timestamp, = struct.unpack('<Q', data[:8])
            self.version_high, = struct.unpack('<B', data[8:9])
            self.version_low, = struct.unpack('<B', data[9:10])
            self.frame_id, = struct.unpack('<B', data[10:11])
            self.frame_packet_count, = struct.unpack('<B', data[11:12])
        except struct.error as e:
            logger.error(f"Failed to unpack PSNInfoPacketHeader: {e}")
            self.timestamp = 0
            self.version_high = 0
            self.version_low = 0
            self.frame_id = 0
            self.frame_packet_count = 0

    def __str__(self):
        return (f"Timestamp: {self.timestamp}, Version High: {self.version_high}, "
                f"Version Low: {self.version_low}, Frame ID: {self.frame_id}, "
                f"Frame Packet Count: {self.frame_packet_count}")

def parse_chunks(data, offset=0):
    chunks = []
    while offset < len(data):
        try:
            chunk_header = PSNChunkHeader(data[offset:offset+4])
            offset += 4
            chunk_data = data[offset:offset + chunk_header.data_len]
            offset += chunk_header.data_len
            if chunk_header.id == 0x6756:
                chunks.append(('PSN_INFO_PACKET', parse_psn_info_packet(chunk_data)))
            # Ignore other chunk types for now...
        except Exception as e:
            logger.error(f"Error parsing chunk: {e}")
            break
    return chunks

def parse_psn_info_packet(data):
    chunks = []
    offset = 0
    while offset < len(data):
        try:
            chunk_header = PSNChunkHeader(data[offset:offset+4])
            offset += 4
            chunk_data = data[offset:offset + chunk_header.data_len]
            offset += chunk_header.data_len
            if chunk_header.id == 0x0000:
                chunks.append(('PSN_INFO_PACKET_HEADER', PSNInfoPacketHeader(chunk_data)))
            elif chunk_header.id == 0x0001:
                chunks.append(('PSN_INFO_SYSTEM_NAME', chunk_data.decode('utf-8').strip('\x00')))
            elif chunk_header.id == 0x0002:
                chunks.append(('PSN_INFO_TRACKER_LIST', parse_psn_info_tracker_list(chunk_data)))
            else:
                chunks.append(('UNKNOWN_CHUNK', chunk_data))
        except Exception as e:
            logger.error(f"Error parsing PSN info packet: {e}")
            break
    return chunks

def parse_psn_info_tracker_list(data):
    chunks = []
    offset = 0
    while offset < len(data):
        try:
            chunk_header = PSNChunkHeader(data[offset:offset+4])
            offset += 4
            chunk_data = data[offset:offset + chunk_header.data_len]
            offset += chunk_header.data_len
            tracker_id = chunk_header.id
            tracker_name = chunk_data.decode('utf-8').strip('\x00').strip()
            chunks.append((tracker_id, tracker_name))
        except Exception as e:
            logger.error(f"Error parsing PSN info tracker list: {e}")
            break
    return chunks

def format_tracker_list(tracker_list):
    formatted_list = []
    for tracker_id, tracker_name in tracker_list:
        formatted_list.append(f"    TrackerID: {tracker_id:<5} Name: {tracker_name}")
    return "\n".join(formatted_list)

# Store available trackers
trackers = {}

def start_udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    logger.info("Starting UDP receiver...")
    while True:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            ip_address = addr[0]
            chunks = parse_chunks(data)
            for chunk_type, chunk_data in chunks:
                if chunk_type == 'PSN_INFO_PACKET':
                    system_name = None
                    tracker_list = []
                    for sub_chunk_type, sub_chunk_data in chunk_data:
                        if sub_chunk_type == 'PSN_INFO_PACKET_HEADER':
                            logger.info(f"  {sub_chunk_type}: {sub_chunk_data}")
                        elif sub_chunk_type == 'PSN_INFO_SYSTEM_NAME':
                            system_name = sub_chunk_data
                            logger.info(f"  PSN_INFO_SYSTEM_NAME: {system_name}")
                        elif sub_chunk_type == 'PSN_INFO_TRACKER_LIST':
                            tracker_list = sub_chunk_data
                            logger.info("  PSN_INFO_TRACKER_LIST:\n" + format_tracker_list(tracker_list))
                        else:
                            logger.info(f"  {sub_chunk_type}: {sub_chunk_data}")

                    # Update the trackers dictionary
                    for tracker_id, tracker_name in tracker_list:
                        trackers[tracker_id] = {
                            'name': tracker_name,
                            'system_name': system_name,
                            'ip_address': ip_address
                        }

                    logger.info(f"Updated trackers: {trackers}")
        except Exception as e:
            logger.error(f"Error receiving data: {e}")

if __name__ == "__main__":
    start_udp_receiver()
