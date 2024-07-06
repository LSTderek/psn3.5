import socket
import struct
import logging
from typing import Tuple, List, Dict

# Define constants
PSN_DATA_TRACKER_POS = 0
CHUNK_ID_TO_STRING = {
    PSN_DATA_TRACKER_POS: 'PSN_DATA_TRACKER_POS'
}

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class PacketProcessor:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def receive_packet(self) -> bytes:
        packet, addr = self.sock.recvfrom(1024)
        logging.debug(f'Received packet from {addr}')
        return packet

    def process_packet(self, packet: bytes):
        try:
            timestamp, version, frame_id, frame_packet_count = self._parse_header(packet)
            logging.debug(f'Packet Timestamp: {timestamp}')
            logging.debug(f'Version: {version}')
            logging.debug(f'Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}')

            offset = 16  # Header size
            while offset < len(packet):
                chunk_id, data_length, has_subchunks = self._parse_chunk(packet, offset)
                chunk_name = CHUNK_ID_TO_STRING.get(chunk_id, f'Unknown chunk ID: {chunk_id}')
                logging.debug(f'Chunk ID: {chunk_id}, Data Length: {data_length}, Has Subchunks: {has_subchunks}')
                
                if chunk_id == PSN_DATA_TRACKER_POS:
                    if data_length != expected_data_length:  # Define or calculate expected_data_length
                        logging.error(f'Unexpected data length for {chunk_name}: {data_length}')
                    else:
                        self._process_psn_data_tracker_pos(packet[offset+8:offset+8+data_length])
                else:
                    logging.debug(f'{chunk_name} with data length: {data_length}')
                
                offset += 8 + data_length  # Move to the next chunk
        except struct.error as e:
            logging.error(f'Struct error during packet processing: {e}')
        except Exception as e:
            logging.error(f'Unexpected error during packet processing: {e}')

    def _parse_header(self, packet: bytes) -> Tuple[int, float, int, int]:
        return struct.unpack('!QfII', packet[:16])

    def _parse_chunk(self, packet: bytes, offset: int) -> Tuple[int, int, int]:
        return struct.unpack('!III', packet[offset:offset+12])

    def _process_psn_data_tracker_pos(self, data: bytes):
        # Placeholder for actual data processing logic
        logging.debug(f'Processing PSN_DATA_TRACKER_POS with data: {data}')

def main():
    processor = PacketProcessor('localhost', 9999)
    while True:
        packet = processor.receive_packet()
        processor.process_packet(packet)

if __name__ == '__main__':
    main()
