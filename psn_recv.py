import socket
import struct
import logging

# PSN multicast address and port
MCAST_GRP = '236.10.10.10'
MCAST_PORT = 56565

# Debug flag
DEBUG = True

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("psn_listener.log"),
        logging.StreamHandler()
    ]
)

# Function to parse PSN data packets
def parse_psn_packet(data):
    try:
        # Unpack the packet header (example header structure)
        packet_header_format = '<Q4B'
        packet_header_size = struct.calcsize(packet_header_format)
        packet_timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from(packet_header_format, data, 0)
        
        # Log packet information
        logging.debug(f"Packet Timestamp: {packet_timestamp}")
        logging.debug(f"Version: {version_high}.{version_low}")
        logging.debug(f"Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Move to the data section (assumed offset after header)
        offset = packet_header_size
        while offset < len(data):
            # Read chunk header (example chunk header structure)
            chunk_header_format = '<IBB'
            chunk_header_size = struct.calcsize(chunk_header_format)
            chunk_id, data_len, has_subchunks = struct.unpack_from(chunk_header_format, data, offset)
            offset += chunk_header_size
            
            logging.debug(f"Chunk ID: {chunk_id}, Data Length: {data_len}, Has Subchunks: {has_subchunks}")

            # Handle different chunk types
            if chunk_id == 0x0000:  # PSN_DATA_TRACKER_POS
                if data_len == 12:  # 3 floats * 4 bytes each
                    pos_x, pos_y, pos_z = struct.unpack_from('<3f', data, offset)
                    print(f"Tracker Position - X: {pos_x}, Y: {pos_y}, Z: {pos_z}")
                else:
                    logging.error(f"Unexpected data length for PSN_DATA_TRACKER_POS: {data_len}")
            elif chunk_id == 0x0001:  # PSN_DATA_TRACKER_SPEED
                if data_len == 12:  # 3 floats * 4 bytes each
                    speed_x, speed_y, speed_z = struct.unpack_from('<3f', data, offset)
                    print(f"Tracker Speed - X: {speed_x}, Y: {speed_y}, Z: {speed_z}")
                else:
                    logging.error(f"Unexpected data length for PSN_DATA_TRACKER_SPEED: {data_len}")
            elif chunk_id == 0x0002:  # PSN_DATA_TRACKER_ORI
                if data_len == 12:  # 3 floats * 4 bytes each
                    ori_x, ori_y, ori_z = struct.unpack_from('<3f', data, offset)
                    print(f"Tracker Orientation - X: {ori_x}, Y: {ori_y}, Z: {ori_z}")
                else:
                    logging.error(f"Unexpected data length for PSN_DATA_TRACKER_ORI: {data_len}")
            else:
                logging.debug(f"Unknown chunk ID: {chunk_id} with data length: {data_len}")

            # Move to the next chunk
            offset += data_len
    except struct.error as e:
        logging.error(f"Error parsing packet: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

def main():
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        # Allow multiple sockets to use the same PORT number
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the multicast address and port
        sock.bind(('', MCAST_PORT))
        
        # Join the multicast group on all interfaces
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        logging.info(f"Listening for PSN data on {MCAST_GRP}:{MCAST_PORT}")
        
        # Receive loop
        while True:
            data, addr = sock.recvfrom(1500)  # Buffer size is 1500 bytes
            logging.debug(f"Received packet from {addr}")
            parse_psn_packet(data)
    except socket.error as e:
        logging.error(f"Socket error: {e}")
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        sock.close()
        logging.info("Socket closed.")

if __name__ == "__main__":
    main()
