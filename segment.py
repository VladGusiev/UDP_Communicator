import struct
import zlib
import random

# all flags values
S = '00000001'  # Syn
A = '00000010'  # Ack
F = '00000100'  # Fin
P = '00001000'  # Push
K = '00010000'  # Keep alive
W = '00100000'  # Switch roles
N = '01000000'  # new stream of data
C = '10000000'  # Complete stream of data

FLAGS = {
    1: "C",
    2: "N",
    3: "W",
    4: "K",
    5: "P",
    6: "F",
    7: "A",
    8: "S"
}

CLIENT_INFO = tuple()

def creating_category(category):
    if category == "1":
        category = 0x01
    elif category == "2":
        category = 0x02
    elif category == "3":
        category = 0x03

    category = struct.pack("!B", category)
    return category


def creating_flags(flags_list):
    if len(flags_list) == 1:
        flags = struct.pack("!B", int(flags_list[0], 2))
    else:
        # add all flags together in binary form, flags is a list of flags
        flags = int(flags_list[0], 2)
        for i in range(1, len(flags_list)):
            flags = flags + int(flags_list[i], 2)
        flags = struct.pack("!B", flags)
    return flags


def creating_fragment_number(fragment_number):
    fragment_number = struct.pack("!H", fragment_number)
    return fragment_number


def creating_checksum(data):
    if random.randint(0, 100) == 1:
        checksum = b'\x00\x00\x00\x00'
        return checksum
    checksum = zlib.crc32(bytes(data, "utf-8"))
    checksum = struct.pack("!I", checksum)
    return checksum


def creating_file_checksum(data):
    if random.randint(0, 100) == 1:
        checksum = b'\x00\x00\x00\x00'
        return checksum
    checksum = zlib.crc32(data)
    checksum = struct.pack("!I", checksum)
    return checksum


def check_checksum(data):
    checksum = data[4:8]
    try:
        message = data[8::].decode("utf-8")
        calculated_checksum = zlib.crc32(bytes(message, "utf-8"))
        calculated_checksum = struct.pack("!I", calculated_checksum)
    except UnicodeDecodeError:
        message = data[8::]
        calculated_checksum = zlib.crc32(message)
        calculated_checksum = struct.pack("!I", calculated_checksum)
    if checksum == calculated_checksum:
        return True
    else:
        return False


def get_flags(flags):
    all_flags = []
    i = 1
    for f in flags:
        if f == "1":
            all_flags.append(FLAGS[i])
        i += 1
    return all_flags