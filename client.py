import socket
import threading
import time
import struct
import os
import zlib
import sys

import segment

CLIENT_IP = "127.0.0.1"
CLIENT_PORT = 50602

SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601

COMMUNICATION_STARTED = False

KEEP_ALIVE_INTERVAL = 5  # seconds
KEEP_ALIVE_MESSAGE = struct.pack("!B", 0x06)

# for resending packets that were not acknowledged
TIMEOUT_INTERVAL = 5  # seconds
UNACKNOWLEDGED_KEEP_LIVE = 0


# all flags values
S = '00000001'  # Syn
A = '00000010'  # Ack
F = '00000100'  # Fin
P = '00001000'  # Push
K = '00010000'  # Keep alive
W = '00100000'  # Switch roles
N = '01000000'  # new stream of data
C = '10000000'  # Complete stream of data

CURRENT_CATEGORY = ""


class Client:
    def __init__(self, ip, port, server_ip, server_port) -> None:
        # self.keep_alive_thread = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket creation

        self.server_ip = server_ip
        self.server_port = server_port

        self.ip = ip
        self.port = port

        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True

    def start_keep_alive(self):
        self.keep_alive_thread.start()

    def keep_alive(self):
        global UNACKNOWLEDGED_KEEP_LIVE
        while True:
            if UNACKNOWLEDGED_KEEP_LIVE == 3:
                print("\nServer is not responding... closing connection")
                break
            else:
                time.sleep(KEEP_ALIVE_INTERVAL)
                if COMMUNICATION_STARTED:
                    self.send_message("1", [K], 'Keep Alive')
                    UNACKNOWLEDGED_KEEP_LIVE += 1
                    self.receive()
            print("CURRENT UNACKNOWLEDGED_KEEP_LIVE: ", UNACKNOWLEDGED_KEEP_LIVE)
        client.quit()

    def receive(self):
        global UNACKNOWLEDGED_KEEP_LIVE

        data = None
        data, self.server = self.socket.recvfrom(1024)  # buffer size is 1024 bytes


        # check if server sent back ack
        if data[0] == 1:
            if "A" in segment.get_flags(format(data[1], "08b")) and "K" in segment.get_flags(
                    format(data[1], "08b")):
                # print("Recieved keep alive ack")
                UNACKNOWLEDGED_KEEP_LIVE = 0
                print("UNACKNOWLEDGED_KEEP_LIVE: ", UNACKNOWLEDGED_KEEP_LIVE)
        return data

    def send_message(self, category, flags, message):

        checksum = segment.creating_checksum(message)
        message = segment.creating_category(category) + segment.creating_flags(flags) + segment.creating_fragment_number(1) + checksum + message.encode("utf-8")

        self.socket.sendto(message, (self.server_ip, self.server_port))

    # QUIT
    def quit(self):
        self.socket.close()
        print("Client closed...")


def system_message():
    print("What type of system message would you like to send?:")
    print("1 -> Switch roles")
    print("2 -> Quit")
    system_message = input("Your choice:")
    if system_message == "1":
        return '1'
    else:
        # CURRENT_CATEGORY = ''
        return '2'


# TODO add fragmenting, sending message about new stram and message about complete stream so sevrer can reassemble
def text_message():
    print("Type you messages here. Type 'xxx' to end sending messages.")
    user_message = input()
    while user_message != "xxx":
        client.send_message(CURRENT_CATEGORY, [P], user_message)
        data = client.receive()
        print(data)
        user_message = input()
    if user_message == "xxx":
        return 'x'


if __name__ == "__main__":
    client = Client(CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
    client.start_keep_alive()
    data = "empty"

    while data != "End connection message recieved... closing connection":
        # global COMMUNICATION_STARTED, CURRENT_CATEGORY
        # establish communication with server and wait for server to send back syn ack. If syn ack is not received in 5 seconds, resend syn
        if not COMMUNICATION_STARTED:
            client.send_message("1", [S], '')
            print("Sending start of communication message")
            while not COMMUNICATION_STARTED:
                data = client.receive()
                if "A" in segment.get_flags(format(data[1], "08b")) and "S" in segment.get_flags(format(data[1], "08b")):
                    print("Recieved start of communication")
                    COMMUNICATION_STARTED = True
                    CURRENT_CATEGORY = ''
                    continue

        else:
            # while user does not input a valid category request for a valid category
            while CURRENT_CATEGORY != "1" and CURRENT_CATEGORY != "2" and CURRENT_CATEGORY != "3" and CURRENT_CATEGORY != "4":
                print("What type of message would you like to send? (text, file)?:")
                print("1 -> System message")
                print("2 -> Text message")
                print("3 -> File message")
                print("4 -> Quit")
                CURRENT_CATEGORY = input("Your choice:" )
            if CURRENT_CATEGORY == "4":
                break

            # if user wants to send a system message
            if CURRENT_CATEGORY == "1":
                type_of_message = system_message()
                if type_of_message == "1":  # switch roles
                    client.send_message(CURRENT_CATEGORY, [W], '')
                    CURRENT_CATEGORY = ''
                    continue
                elif type_of_message == "2":
                    CURRENT_CATEGORY = ''
                    continue

            # if user wants to send a text message
            elif CURRENT_CATEGORY == "2":
                client.send_message(CURRENT_CATEGORY, [N], 'fragment size info will be here')  # sending message about new stream
                if text_message() == 'x':
                    client.send_message(CURRENT_CATEGORY, [C], '')  # sending message about complete stream
                    CURRENT_CATEGORY = ''
                    continue

        # TODO ADD FILE SENDING
        # print("Input your message: ")
        # client.send_message(CURRENT_CATEGORY, input())
        # data = client.receive()
        # print(data)

    client.quit()
