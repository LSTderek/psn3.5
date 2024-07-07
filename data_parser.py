import logging
import struct
from multiprocessing.connection import Listener

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
    # class definition remains the same
    ...

class PSNDataPacketHeader:
    # class definition based on the image provided
    ...

def parse_psn_data_packet(data):
    # function to parse data packets based on the given structure
    ...

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

if __name__ == "__main__":
    start_data_parser()
