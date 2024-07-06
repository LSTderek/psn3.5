import socket
import struct

# Constants
MCAST_GRP = '236.10.10.10'
MCAST_PORT = 56565
PSN_INFO_TYPE = b'\x44\x53\x52\x20'  # Example PSN_INFO chunk type, replace with the correct one

def parse_packet(packet):
    index = 0
    packet_len = len(packet)
    while index < packet_len:
        # Extract chunk type and size
        chunk_type = packet[index:index + 4]
        chunk_size = struct.unpack('>I', packet[index + 4:index + 8])[0]
        chunk_data = packet[index + 8:index + 8 + chunk_size]

        # Check if the chunk is PSN_INFO
        if chunk_type == PSN_INFO_TYPE:
            print("PSN_INFO chunk found.")
            print(f"Chunk data: {chunk_data}")
            # Add further parsing logic for PSN_INFO chunk if needed
            return True
        
        # Move to the next chunk
        index += 8 + chunk_size
    
    return False

def main():
    # Set up the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Listening for PSN packets on {MCAST_GRP}:{MCAST_PORT}...")

    while True:
        packet, addr = sock.recvfrom(10240)
        print(f"Received packet from {addr}")
        print(f"Raw packet data: {packet.hex()}")
        if not parse_packet(packet):
            print("No PSN_INFO chunk found.")

if __name__ == "__main__":
    main()
