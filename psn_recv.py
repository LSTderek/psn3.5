import socket
import struct
from collections import namedtuple, defaultdict

# Define the multicast address and port for PSN
MULTICAST_GROUP = '236.10.10.10'
PORT = 56565

# Define structures for decoding packets
PacketHeader = namedtuple('PacketHeader', 'id length flags sequence_number timestamp')
InfoPacket = namedtuple('InfoPacket', 'header system_name tracker_names')

def create_socket():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    # Allow multiple sockets to use the same PORT number
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the server address
    sock.bind(('', PORT))
    
    # Tell the operating system to add the socket to the multicast group on all interfaces
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    return sock

def decode_packet(data):
    if len(data) < 20:
        return None
    
    header = PacketHeader._make(struct.unpack('!HHBBQ', data[:20]))
    
    if header.id != 1:  # Assuming 1 is the ID for info packets
        return None
    
    offset = 20
    system_name_len = struct.unpack('!H', data[offset:offset+2])[0]
    offset += 2
    system_name = data[offset:offset+system_name_len].decode('utf-8')
    offset += system_name_len
    
    tracker_count = struct.unpack('!H', data[offset:offset+2])[0]
    offset += 2
    tracker_names = {}
    
    for _ in range(tracker_count):
        tracker_id = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        tracker_name_len = struct.unpack('!H', data[offset:offset+2])[0]
        offset += 2
        tracker_name = data[offset:offset+tracker_name_len].decode('utf-8')
        offset += tracker_name_len
        tracker_names[tracker_id] = tracker_name
    
    return InfoPacket(header, system_name, tracker_names)

def listen_for_psn_packets():
    sock = create_socket()
    fragments = defaultdict(lambda: defaultdict(bytes))

    print("Listening for PSN packets on all interfaces...")

    while True:
        data, address = sock.recvfrom(1500)  # Buffer size is 1500 bytes, the maximum size for a single UDP packet
        packet = decode_packet(data)
        if packet:
            print_info(packet)

def print_info(info):
    print("Received PSN Info Packet:")
    print(f"System Name: {info.system_name}")
    print("Tracker Names:")
    for tracker_id, tracker_name in info.tracker_names.items():
        print(f"  ID: {tracker_id}, Name: {tracker_name}")

if __name__ == "__main__":
    listen_for_psn_packets()
