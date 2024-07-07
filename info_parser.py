import logging
import struct
import re
from multiprocessing.connection import Listener

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = True
LOG_FILE = 'info_parser.log'

# Set up logging
logger = logging.getLogger('InfoParser')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if LOG_TO_FILE:
    file_handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5)
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
            tracker_name = re.sub(r'[^\x20-\x7E]+', '', chunk_data.decode('utf-8')).strip()
            chunks.append((tracker_name, tracker_id))
        except Exception as e:
            logger.error(f"Error parsing PSN info tracker list: {e}")
            break
    return chunks

def format_tracker_list(tracker_list):
    formatted_list = []
    for tracker_name, tracker_id in tracker_list:
        formatted_list.append(f"    TrackerID: {tracker_id:<5} Name: {tracker_name}")
    return "\n".join(formatted_list)

def start_info_parser():
    listener = Listener(('localhost', 6000), authkey=b'psn_secret_key')
    logger.info("InfoParser started and waiting for connections...")
    while True:
        with listener.accept() as conn:
            logger.info('Connection accepted from receiver')
            while True:
                try:
                    packet = conn.recv()
                    if packet == 'CLOSE':
                        break
                    parsed_info = parse_psn_info_packet(packet)
                    for sub_chunk_type, sub_chunk_data in parsed_info:
                        if sub_chunk_type == 'PSN_INFO_PACKET_HEADER':
                            logger.info(f"  {sub_chunk_type}: {sub_chunk_data}")
                        elif sub_chunk_type == 'PSN_INFO_SYSTEM_NAME':
                            logger.info(f"  PSN_INFO_SYSTEM_NAME: {sub_chunk_data}")
                        elif sub_chunk_type == 'PSN_INFO_TRACKER_LIST':
                            logger.info("  PSN_INFO_TRACKER_LIST:\n" + format_tracker_list(sub_chunk_data))
                        else:
                            logger.info(f"  {sub_chunk_type}: {sub_chunk_data}")
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Error processing packet: {e}")
                    break

if __name__ == "__main__":
    start_info_parser()