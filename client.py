import socket
import threading
import time
import struct
import os
import zlib

CLIENT_IP = "127.0.0.1"
CLIENT_PORT = 50602

SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601

KEEP_ALIVE_INTERVAL = 5  # seconds
KEEP_ALIVE_MESSAGE = struct.pack("!B", 0x06)


# all flags values
S = '00000001'  # Syn
A = '00000010'  # Ack
F = '00000100'  # Fin
P = '00001000'  # Push
K = '00010000'  # Keep alive
W = '00100000'  # Switch roles
N = '01000000'  # new stream of data
C = '10000000'  # Complete stream of data


class Client:
    def __init__(self, ip, port, server_ip, server_port) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket creation

        self.server_ip = server_ip
        self.server_port = server_port

        self.ip = ip
        self.port = port

    def receive(self):
        data = None
        data, self.server = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
        return str(data, encoding="utf-8")

    def send_message(self, category, message):
        # message = self.creating_checksum(message)
        # message = str('{0:032b}'.format(message))
        message = self.creating_category(category) + self.creating_flags([A, S, K, W]) + message.encode("utf-8")
        # message = bytes(message, encoding="utf-8")
        self.socket.sendto(message, (self.server_ip, self.server_port))

    # creating header consisting of category, falgs, fragment number, and checksum
    # Category will contain the type of message being sent 0x01 for system messages like keep alive, syn, fin, etc.
    # 0x02 for text messages and 0x03 for file messages
    # Flags will contain the flags for the message like ACK, SYN, FIN, where each flag is a bit in the flags byte
    # Fragment number will contain the number of the fragment being sent
    # Checksum will contain the checksum of the message being sent
    def creating_category(self, category):
        if category == "1":
            category = 0x01
        elif category == "2":
            category = 0x02
        elif category == "3":
            category = 0x03

        category = struct.pack("!B", category)
        return category

    def creating_flags(self, flags_list):
        if len(flags_list) == 1:
            flags = struct.pack("!B", flags_list[0])
        else:
            # add all flags together in binary form, flags is a list of flags
            flags = int(flags_list[0], 2)
            for i in range(1, len(flags_list)):
                flags = flags + int(flags_list[i], 2)
            flags = struct.pack("!B", flags)
        return flags





    # def creating_checksum(self, data):
    #     print("original data: ", data)
    #     print("crc32: ", zlib.crc32(bytes(data, "utf-8")))
    #     checksum = zlib.crc32(bytes(data, "utf-8"))
    #     checksum = str('{0:032b}'.format(checksum))
    #     checksum = bytes(int(checksum[i: i + 8], 2) for i in range(0, len(checksum), 8))
    #
    #     return checksum

    # # KEEP ALIVE
    # def keep_alive(self):
    #     while True:
    #         self.socket.sendto(KEEP_ALIVE_MESSAGE, (self.server_ip, self.server_port))
    #         time.sleep(KEEP_ALIVE_INTERVAL)
    #
    # def start_keep_alive(self):
    #     self.keep_alive_thread = threading.Thread(target=self.keep_alive)
    #     self.keep_alive_thread.start()

    # QUIT
    def quit(self):
        self.socket.close()
        print("Client closed...")


if __name__ == "__main__":
    client = Client(CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
    # client.start_keep_alive()
    data = "empty"

    while data != "End connection message recieved... closing connection":
        category = ""

        # while user does not input a valid category request for a valid category
        while category != "1" and category != "2" and category != "3":
            print("What type of message would you like to send? (text, file)?:")
            print("1 -> System message")
            print("2 -> Text message")
            print("3 -> File message")
            category = input("Your choice:" )

        print("Input your message: ")
        client.send_message(category, input())
        data = client.receive()
        print(data)

    client.quit()
