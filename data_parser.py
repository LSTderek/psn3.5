import logging
from multiprocessing.connection import Listener

# Configuration for logging
logger = logging.getLogger('DataParser')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def start_data_parser():
    address = ('localhost', 6000)
    listener = Listener(address, authkey=b'secret')
    logger.info("DataParser started and waiting for connections...")
    while True:
        with listener.accept() as conn:
            logger.info(f"Connection accepted from {listener.last_accepted}")
            try:
                while True:
                    data = conn.recv()
                    if not data:
                        break
                    logger.info(f"Received PSN_DATA_PACKET: {data}")
            except EOFError:
                logger.info("Connection closed")

if __name__ == "__main__":
    start_data_parser()
