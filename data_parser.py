import logging
import struct
from multiprocessing.connection import Listener, Client

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = True
LOG_FILE = 'data_parser.log'

# Set up logging
logger = logging.getLogger('DataParser')
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

class PSNDataPacketHeader:
    def __init__(self, data):
        try:
            self.packet_timestamp, = struct.unpack('<Q', data[:8])
            self.version_high, = struct.unpack('<B', data[8:9])
            self.version_low, = struct.unpack('<B', data[9:10])
            self.frame_id, = struct.unpack('<B', data[10:11])
            self.frame_packet_count, = struct.unpack('<B', data[11:12])
        except struct.error as e:
            logger.error(f"Failed to unpack PSNDataPacketHeader: {e}")
            self.packet_timestamp = 0
            self.version_high = 0
            self.version_low = 0
            self.frame_id = 0
            self.frame_packet_count = 0

    def __str__(self):
        return (f"Packet Timestamp: {self.packet_timestamp}, Version High: {self.version_high}, "
                f"Version Low: {self.version_low}, Frame ID: {self.frame_id}, "
                f"Frame Packet Count: {self.frame_packet_count}")

def parse_psn_data_packet(data):
    chunks = []
    offset = 0
    while offset < len(data):
        try:
            chunk_header = PSNChunkHeader(data[offset:offset+4])
            offset += 4
            chunk_data = data[offset:offset + chunk_header.data_len]
            offset += chunk_header.data_len
            if chunk_header.id == 0x0000:
                chunks.append(('PSN_DATA_PACKET_HEADER', PSNDataPacketHeader(chunk_data)))
            else:
                chunks.append(('UNKNOWN_CHUNK', chunk_data))
        except Exception as e:
            logger.error(f"Error parsing PSN data packet: {e}")
            break
    return chunks

def start_data_parser():
    listener = Listener(('localhost', 6001))

    logger.info("Starting Data Packet Parser...")
    while True:
        conn = listener.accept()
        logger.info("Connection accepted from: %s" % str(listener.last_accepted))
        while True:
            try:
                data = conn.recv()
                if not data:
                    break
                chunks = parse_psn_data_packet(data)
                logger.info(f"Parsed Data Packet: {chunks}")
                conn.send(chunks)
            except Exception as e:
                logger.error(f"Error parsing data packet: {e}")
                conn.close()
                break

if __name__ == "__main__":
    start_data_parser()
