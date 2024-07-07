import socket
import struct
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing.connection import Client
import re

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
MAX_PACKET_SIZE = 1500

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = True
DISPLAY_TRACKER_UPDATES = True
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

def parse_chunks(data, offset=0):
    chunks = []
    while offset < len(data):
        try:
            chunk_header = PSNChunkHeader(data[offset:offset+4])
            offset += 4
            chunk_data = data[offset:offset + chunk_header.data_len]
            offset += chunk_header.data_len
            if chunk_header.id == 0x6756:
                chunks.append(('PSN_INFO_PACKET', chunk_data))
            else:
                chunks.append(('UNKNOWN_CHUNK', chunk_data))
        except Exception as e:
            logger.error(f"Error parsing chunk: {e}")
            break
    return chunks

def start_udp_receiver(enable_info_parser=True, enable_data_parser=True):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    info_conn = None
    data_conn = None

    if enable_info_parser:
        try:
            info_conn = Client(('localhost', 6000), authkey=b'psn_secret_key')
            logger.info("Connected to Info Parser")
        except ConnectionRefusedError:
            logger.error("Info Parser is not available")

    if enable_data_parser:
        try:
            data_conn = Client(('localhost', 6001), authkey=b'psn_secret_key')
            logger.info("Connected to Data Parser")
        except ConnectionRefusedError:
            logger.error("Data Parser is not available")

    logger.info("Starting UDP receiver...")
    while True:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            ip_address = addr[0]
            logger.info(f"Received packet from {ip_address}")

            chunks = parse_chunks(data)
            for chunk_type, chunk_data in chunks:
                if chunk_type == 'PSN_INFO_PACKET' and info_conn:
                    try:
                        info_conn.send(chunk_data)
                        logger.info("Sent PSN_INFO_PACKET to Info Parser")
                    except Exception as e:
                        logger.error(f"Failed to send to Info Parser: {e}")
                        info_conn = None
                elif chunk_type == 'UNKNOWN_CHUNK' and data_conn:
                    try:
                        data_conn.send(chunk_data)
                        logger.info("Sent UNKNOWN_CHUNK to Data Parser")
                    except Exception as e:
                        logger.error(f"Failed to send to Data Parser: {e}")
                        data_conn = None
        except Exception as e:
            logger.error(f"Error receiving data: {e}")

if __name__ == "__main__":
    start_udp_receiver(enable_info_parser=True, enable_data_parser=False)
