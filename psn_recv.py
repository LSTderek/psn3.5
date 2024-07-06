import socket
import struct
import logging

# PSN multicast address and port
MCAST_GRP = '236.10.10.10'
MCAST_PORT = 56565

# Debug flag
DEBUG = True

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to parse PSN data packets
def parse_psn_packet(data):
    try:
        # Unpack the packet header (example header structure)
        packet_timestamp, version_high, version_low, frame_id, frame_packet_count = struct.unpack_from('<Q4B', data, 0)
        
        # Print packet information
        logging.debug(f"Packet Timestamp: {packet_timestamp}")
        logging.debug(f"Version: {version_high}.{version_low}")
        logging.debug(f"Frame ID: {frame_id}, Frame Packet Count: {frame_packet_count}")

        # Move to the data section (assumed offset after header)
        offset = 16
        while offset < len(data):
            # Read chunk header (example chunk header structure)
            chunk_id, data_len, has_subchunks = struct.unpack_from('<IBB', data, offset)
            offset += 6
            
            # Handle different chunk types
            if chunk_id == 0x0000:  # PSN_DATA_TRACKER_POS
                pos_x, pos_y, pos_z = struct.unpack_from('<3f', data, offset)
                print(f"Tracker Position - X: {pos_x}, Y: {pos_y}, Z: {pos_z}")
            elif chunk_id == 0x0001:  # PSN_DATA_TRACKER_SPEED
                speed_x, speed_y, speed_z = struct.unpack_from('<3f', data, offset)
                print(f"Tracker Speed - X: {speed_x}, Y: {speed_y}, Z: {speed_z}")
            elif chunk_id == 0x0002:  # PSN_DATA_TRACKER_ORI
                ori_x, ori_y, ori_z = struct.unpack_from('<3f', data, offset)
                print(f"Tracker Orientation - X: {ori_x}, Y: {ori_y}, Z: {ori_z}")
            
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
