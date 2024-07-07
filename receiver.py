import socket
import struct
import logging
from multiprocessing.connection import Client, Listener

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
MAX_PACKET_SIZE = 1500

# Configuration for logging
LOG_TO_FILE = False
LOG_TO_CONSOLE = True
LOG_FILE = 'receiver.log'

# Set up logging
logger = logging.getLogger('Receiver')
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

def start_udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP, PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    info_parser = Client(('localhost', 6000))
    data_parser = Client(('localhost', 6001))

    logger.info("Starting UDP receiver...")
    while True:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            ip_address = addr[0]
            logger.info(f"Received raw packet from {ip_address}: {data}")

            # Determine the packet type and forward to appropriate parser
            if data[0] == 0x6756:  # Example condition for info packet
                info_parser.send(data)
            else:
                data_parser.send(data)
        except Exception as e:
            logger.error(f"Error receiving data: {e}")

if __name__ == "__main__":
    start_udp_receiver()
