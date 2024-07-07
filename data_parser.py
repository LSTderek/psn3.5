import logging
import socket
import struct
from multiprocessing.connection import Listener

# Configuration for logging
LOG_FILE = 'data_parser.log'
LOG_TO_CONSOLE = True

# Set up logging
logger = logging.getLogger('DataParser')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def start_data_parser():
    address = ('localhost', 6000)
    listener = Listener(address, authkey=b'secretkey')
    logger.info("DataParser started and waiting for connections...")
    
    while True:
        with listener.accept() as conn:
            logger.info('Connection accepted from %s', listener.last_accepted)
            while True:
                try:
                    packet = conn.recv()
                    if packet is None:
                        break
                    logger.info(f"Received raw data packet: {packet}")
                except EOFError:
                    break

if __name__ == "__main__":
    start_data_parser()
