import struct
import zlib

# all flags values
S = '00000001'  # Syn
A = '00000010'  # Ack
F = '00000100'  # Fin
P = '00001000'  # Push
K = '00010000'  # Keep alive
W = '00100000'  # Switch roles
N = '01000000'  # new stream of data
C = '10000000'  # Complete stream of data


# creating header consisting of category, falgs, fragment number, and checksum
# Category will contain the type of message being sent 0x01 for system messages like keep alive, syn, fin, etc.
# 0x02 for text messages and 0x03 for file messages
# Flags will contain the flags for the message like ACK, SYN, FIN, where each flag is a bit in the flags byte
# Fragment number will contain the number of the fragment being sent
# Checksum will contain the checksum of the message being sent

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


# fragment number will take 2 bytes to represent the fragment number
def creating_fragment_number(fragment_number):
    fragment_number = struct.pack("!H", fragment_number)
    return fragment_number


def creating_checksum(data):
    checksum = zlib.crc32(bytes(data, "utf-8"))
    checksum = struct.pack("!I", checksum)
    return checksum


def check_checksum(data):
    checksum = data[4:8]
    message = data[8::].decode("utf-8")
    calculated_checksum = creating_checksum(message)
    if checksum == calculated_checksum:
        return True
    else:
        return False