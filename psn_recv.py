import socket
import struct

MULTICAST_GROUP = '236.10.10.10'
PORT = 56565
BUFFER_SIZE = 1500

# Create the UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to the server address
sock.bind(('', PORT))

# Tell the operating system to add the socket to the multicast group on all interfaces.
mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

print(f"Listening for PSN packets on {MULTICAST_GROUP}:{PORT}...")

# Define chunk type identifiers
CHUNK_TYPE_INFO_PACKET = 0x6756
CHUNK_TYPE_INFO_PACKET_HEADER = 0x0000
CHUNK_TYPE_INFO_SYSTEM_NAME = 0x0001
CHUNK_TYPE_INFO_TRACKER_LIST = 0x0002
CHUNK_TYPE_INFO_TRACKER_NAME = 0x0000

def decode_uint64(data, offset):
    return struct.unpack_from('<Q', data, offset)[0], offset + 8

def decode_uint8(data, offset):
    return struct.unpack_from('<B', data, offset)[0], offset + 1

def decode_char_array(data, offset, length):
    return data[offset:offset + length].decode('ascii'), offset + length

def decode_chunk_header(data, offset):
    chunk_type, chunk_length = struct.unpack_from('<HI', data, offset)
    return chunk_type, chunk_length, offset + 6

def decode_info_packet_header(data, offset):
    packet_timestamp, offset = decode_uint64(data, offset)
    version_high, offset = decode_uint8(data, offset)
    version_low, offset = decode_uint8(data, offset)
    frame_id, offset = decode_uint8(data, offset)
    frame_packet_count, offset = decode_uint8(data, offset)
    header = {
        'packet_timestamp': packet_timestamp,
        'version_high': version_high,
        'version_low': version_low,
        'frame_id': frame_id,
        'frame_packet_count': frame_packet_count,
    }
    return header, offset

def decode_info_system_name(data, offset, length):
    system_name, offset = decode_char_array(data, offset, length)
    return system_name, offset

def decode_info_tracker_name(data, offset, length):
    tracker_name, offset = decode_char_array(data, offset, length)
    return tracker_name, offset

def decode_info_tracker_list(data, offset, length):
    end = offset + length
    tracker_list = []

    while offset < end:
        tracker_chunk_type, tracker_chunk_length, offset = decode_chunk_header(data, offset)
        if tracker_chunk_type == CHUNK_TYPE_INFO_TRACKER_NAME:
            tracker_name, offset = decode_info_tracker_name(data, offset, tracker_chunk_length)
            tracker_list.append(tracker_name)
        else:
            offset += tracker_chunk_length  # Skip unknown tracker chunk

    return tracker_list, offset

def decode_info_chunk(data, offset, length):
    end = offset + length
    info = {}

    while offset < end:
        chunk_type, chunk_length, offset = decode_chunk_header(data, offset)
        if chunk_type == CHUNK_TYPE_INFO_PACKET_HEADER:
            info_header, offset = decode_info_packet_header(data, offset)
            info['header'] = info_header
        elif chunk_type == CHUNK_TYPE_INFO_SYSTEM_NAME:
            system_name, offset = decode_info_system_name(data, offset, chunk_length)
            info['system_name'] = system_name
        elif chunk_type == CHUNK_TYPE_INFO_TRACKER_LIST:
            tracker_list, offset = decode_info_tracker_list(data, offset, chunk_length)
            info['tracker_list'] = tracker_list
        else:
            offset += chunk_length  # Skip unknown chunk

    return info, offset

def decode_chunk(data, offset=0):
    chunks = {}
    while offset < len(data):
        if offset + 6 > len(data):
            break
        chunk_type, chunk_length, offset = decode_chunk_header(data, offset)

        if offset + chunk_length > len(data):
            break

        if chunk_type == CHUNK_TYPE_INFO_PACKET:
            info, offset = decode_info_chunk(data, offset, chunk_length)
            chunks['info'] = info
        else:
            print(f"Unknown chunk type: {chunk_type}, skipping...")
            offset += chunk_length

    return chunks

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    print(f"Received packet from {addr}")

    chunks = decode_chunk(data)
    if 'info' in chunks:
        print("Extracted Info:", chunks['info'])
