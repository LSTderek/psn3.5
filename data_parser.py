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
                        logger.info(f"Received PSN_DATA_PACKET: {data}")
                except EOFError:
                    logger.info("Connection closed")
                    break


if __name__ == "__main__":
    start_data_parser()
