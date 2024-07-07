import logging
from logging.handlers import RotatingFileHandler
from multiprocessing.connection import Listener
import struct

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

def start_data_parser():
    address = ('localhost', 6000)
    listener = Listener(address, authkey=b'data_parser')
    logger.info("DataParser started and waiting for connections...")

    while True:
        with listener.accept() as conn:
            logger.info('Connection accepted from ' + str(listener.last_accepted))
            while True:
                try:
                    data = conn.recv()
                    if data:
                        header = PSNDataPacketHeader(data[:12])
                        remaining_data = data[12:]
                        logger.info(f"Parsed Data Packet Header: {header}")
                        logger.info(f"Remaining Raw Data: {remaining_data}")
                except EOFError:
                    logger.info("Connection closed")
                    break

if __name__ == "__main__":
    start_data_parser()
