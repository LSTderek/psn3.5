import socket
import struct
import logging
from logging.handlers import RotatingFileHandler
from multiprocessing.connection import Client

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
MAX_PACKET_SIZE = 1500

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = True
DISPLAY_TRACKER_UPDATES = True
ENABLE_INFO_PARSER = True
ENABLE_DATA_PARSER = False
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

def start_udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    info_parser_conn = None
    data_parser_conn = None

    if ENABLE_INFO_PARSER:
        info_parser_conn = Client(('localhost', 6000))
    if ENABLE_DATA_PARSER:
        data_parser_conn = Client(('localhost', 6001))

    logger.info("Starting UDP receiver...")
    while True:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            ip_address = addr[0]
            logger.info(f"Received raw packet from {ip_address}: {data}")
            chunk_header = PSNChunkHeader(data[:4])
            
            if chunk_header.id == 0x6756 and ENABLE_INFO_PARSER:
                info_parser_conn.send(data)
                parsed_info = info_parser_conn.recv()
                logger.info(f"Parsed Info Packet: {parsed_info}")
            elif chunk_header.id == 0x1234 and ENABLE_DATA_PARSER:
                data_parser_conn.send(data)
                parsed_data = data_parser_conn.recv()
                logger.info(f"Parsed Data Packet: {parsed_data}")
            else:
                logger.info(f"Unhandled packet type with chunk ID: {chunk_header.id}")
        except Exception as e:
            logger.error(f"Error receiving data: {e}")

if __name__ == "__main__":
    start_udp_receiver()
