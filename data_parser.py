import logging
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
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

if LOG_TO_CONSOLE:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def start_data_parser():
    address = ('localhost', 6001)  # Address and port to listen on
    listener = Listener(address, authkey=b'secret password')

    logger.info("DataParser started and waiting for connections...")
    while True:
        try:
            with listener.accept() as conn:
                logger.info(f"Connection accepted from {listener.last_accepted}")
                while True:
                    data = conn.recv()
                    logger.info(f"Received raw data: {data}")
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    start_data_parser()
