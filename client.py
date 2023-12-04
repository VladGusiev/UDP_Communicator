import socket
import threading
import time
import struct
import os
import zlib
import sys

import segment
import handler

# CLIENT_IP = "127.0.0.1"
# CLIENT_PORT = 50602
#
# SERVER_IP = "127.0.0.1"
# SERVER_PORT = 50601

COMMUNICATION_STARTED = False
COMMUNICATION_TERMINATED = False

# for sending keep alive messages
KEEP_ALIVE_INTERVAL = 5  # seconds (bigger number faster transmission)
UNACKNOWLEDGED_KEEP_LIVE = 0
MAX_UNACKNOWLEDGED_KEEP_LIVE = 5
CLIENT_TIMED_OUT = False

# for resending packets that were not acknowledged
SEGMENT_RESEND_INTERVAL = 0.5  # seconds
IS_WAITING_FOR_ACK = False

CURRENT_UNACKNOWLEDGED_SEGMENTS = 0
MAX_UNACKNOWLEDGED_SEGMENTS = 5

SWAP_ROLES = False


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
    def __init__(self, server_ip, server_port) -> None:
        # self.keep_alive_thread = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket creation
        self.socket.settimeout(0)

        self.server_ip = server_ip
        self.server_port = server_port

        # self.ip = ip
        # self.port = port

        self.keep_alive_thread = threading.Thread(target=self.keep_alive)
        self.keep_alive_thread.daemon = True

    def start_keep_alive(self):
        self.keep_alive_thread.start()

    def keep_alive(self):
        global UNACKNOWLEDGED_KEEP_LIVE, CLIENT_TIMED_OUT, COMMUNICATION_TERMINATED, COMMUNICATION_STARTED, SWAP_ROLES
        while not COMMUNICATION_TERMINATED:
            if SWAP_ROLES:
                self.keep_alive_thread.join()
            if UNACKNOWLEDGED_KEEP_LIVE >= 5:
                print("\nServer is not responding... closing connection")
                CLIENT_TIMED_OUT = True
                COMMUNICATION_TERMINATED = True
                break
            else:
                if COMMUNICATION_STARTED:
                    # TODO this does not work because the server is closed and the client is still trying to send keep alive messages
                    time.sleep(KEEP_ALIVE_INTERVAL)
                    if COMMUNICATION_STARTED:
                        self.send_message("1", [K], 1, 'Keep Alive')
                        UNACKNOWLEDGED_KEEP_LIVE += 1
                        self.receive()
                    # print("CURRENT UNACKNOWLEDGED_KEEP_LIVE: ", UNACKNOWLEDGED_KEEP_LIVE)
        # self.keep_alive_thread.join()
        self.quit()

    def receive(self):
        global UNACKNOWLEDGED_KEEP_LIVE, COMMUNICATION_TERMINATED, IS_WAITING_FOR_ACK, CURRENT_UNACKNOWLEDGED_SEGMENTS, COMMUNICATION_STARTED, SWAP_ROLES
        data = None
        try:
            while data is None:
                data, self.server = self.socket.recvfrom(1472)

            if IS_WAITING_FOR_ACK:
                # print("is was here")
                if data[0] == 2 or data[0] == 3:
                    if "A" in segment.get_flags(format(data[1], "08b")) and "P" in segment.get_flags(
                            format(data[1], "08b")):
                        IS_WAITING_FOR_ACK = False
                        CURRENT_UNACKNOWLEDGED_SEGMENTS = 0
                        print("Received ack for text/file message")
                # check if server sent back ack for keep alive message
                if data[0] == 1:
                    if "A" in segment.get_flags(format(data[1], "08b")) and "S" in segment.get_flags(
                            format(data[1], "08b")):
                        print("Recieved start of communication")
                        COMMUNICATION_STARTED = True
                        IS_WAITING_FOR_ACK = False

                    if "A" in segment.get_flags(format(data[1], "08b")) and "F" in segment.get_flags(format(data[1], "08b")):
                        print("Received acknowledge to end of communication")
                        COMMUNICATION_TERMINATED = True
                        self.quit()
            if data[0] == 1:
                if "A" in segment.get_flags(format(data[1], "08b")) and "K" in segment.get_flags(
                        format(data[1], "08b")):
                    # print("Received keep alive ack")
                    UNACKNOWLEDGED_KEEP_LIVE = 0
                    # print("UNACKNOWLEDGED_KEEP_LIVE: ", UNACKNOWLEDGED_KEEP_LIVE)
                if "A" in segment.get_flags(format(data[1], "08b")) and "W" in segment.get_flags(
                        format(data[1], "08b")):
                    print("Received swap confirmation")
                    COMMUNICATION_TERMINATED = True
                    COMMUNICATION_STARTED = False
                    IS_WAITING_FOR_ACK = False
                    SWAP_ROLES = True
                    self.quit()
                if "W" in segment.get_flags(format(data[1], "08b")):
                    self.send_message('1', [A, W], 1, 'Switch roles acknowledge')
                    print("Received swap request")
                    COMMUNICATION_TERMINATED = True
                    COMMUNICATION_STARTED = False
                    IS_WAITING_FOR_ACK = False
                    SWAP_ROLES = True
                    self.quit()
            return data

        except socket.error:
            ...
            # print("Server is not responding... closing connection")
            # self.quit()

    # TODO add fragmenting, sending message about new stram and message about complete stream so server can reassemble
    def send_text_message(self):
        global CURRENT_CATEGORY, IS_WAITING_FOR_ACK, MAX_UNACKNOWLEDGED_SEGMENTS, SEGMENT_RESEND_INTERVAL, CLIENT_TIMED_OUT, COMMUNICATION_TERMINATED, CURRENT_UNACKNOWLEDGED_SEGMENTS

        current_fragment_number = 0
        fragment_size = input("Input fragment size: ")
        while not fragment_size.isdigit():
            print("Fragment size must be a number")
            fragment_size = input("Input fragment size: ")
        while int(fragment_size) > 1464:
            print("Fragment size must be less than 1464")
            fragment_size = input("Input fragment size: ")

        fragment_size = int(fragment_size)

        self.send_message(CURRENT_CATEGORY, [N], current_fragment_number,
                            'fragment size info will be here')  # sending message about new stream

        print("Input your message: ")
        # sending message to server
        user_message = input()

        # fragmenting message
        fragments = []
        for i in range(0, len(user_message), fragment_size):
            fragments.append(user_message[i:i + fragment_size])

        # sending fragments
        for i in range(len(fragments)):
            self.send_message(CURRENT_CATEGORY, [P], i+1, fragments[i])
            IS_WAITING_FOR_ACK = True

            # waiting for ack
            segment_sent_time = time.time()
            while IS_WAITING_FOR_ACK:
                if CURRENT_UNACKNOWLEDGED_SEGMENTS >= MAX_UNACKNOWLEDGED_SEGMENTS:
                    # print("Server is not responding... closing connection")
                    CLIENT_TIMED_OUT = True
                    COMMUNICATION_TERMINATED = True
                    break
                if time.time() - segment_sent_time >= SEGMENT_RESEND_INTERVAL:
                    print("Resending text message...")
                    self.send_message(CURRENT_CATEGORY, [P], i+1, fragments[i])
                    segment_sent_time = time.time()
                # time.sleep(1)

                self.receive()
            current_fragment_number += 1

        self.send_message(CURRENT_CATEGORY, [C], current_fragment_number,  'End of transmission')  # sending message about complete stream

    def send_message(self, category, flags, frag_num, message):

        checksum = segment.creating_checksum(message)
        message = segment.creating_category(category) + segment.creating_flags(flags) + segment.creating_fragment_number(frag_num) + checksum + message.encode("utf-8")

        self.socket.sendto(message, (self.server_ip, self.server_port))

    # C:\Users\someuser\Desktop\pypy_40k_2.png
    def send_message_file_format(self, category, flags, frag_num, message):
        checksum = segment.creating_file_checksum(message)
        message = segment.creating_category(category) + segment.creating_flags(
            flags) + segment.creating_fragment_number(frag_num) + checksum + message

        self.socket.sendto(message, (self.server_ip, self.server_port))

    def send_file_message(self):
        global CURRENT_CATEGORY, IS_WAITING_FOR_ACK, MAX_UNACKNOWLEDGED_SEGMENTS, SEGMENT_RESEND_INTERVAL, CLIENT_TIMED_OUT, COMMUNICATION_TERMINATED, CURRENT_UNACKNOWLEDGED_SEGMENTS

        file_path = input("Input file path: ")
        while not os.path.isfile(file_path):
            print("File does not exist")
            file_path = input("Input file path: ")

        file_size = os.path.getsize(file_path)
        print("File size: ", file_size)

        file = open(file_path, "rb")

        # sending message about new stream
        self.send_message(CURRENT_CATEGORY, [N], 0, os.path.basename(file_path))

        # sending file
        current_fragment_number = 1

        fragment_size = input("Input fragment size: ")
        while not fragment_size.isdigit():
            print("Fragment size must be a number")
            fragment_size = input("Input fragment size: ")
        while int(fragment_size) > 1464:
            print("Fragment size must be less than 1464")
            fragment_size = input("Input fragment size: ")

        fragment_size = int(fragment_size)


        fragments = []
        for i in range(0, file_size, fragment_size):
            fragments.append(file.read(fragment_size))
        print("Number of fragments: ", len(fragments))

        # sending fragments
        for i in range(len(fragments)):
            self.send_message_file_format(CURRENT_CATEGORY, [P], i + 1, fragments[i])
            IS_WAITING_FOR_ACK = True

            # waiting for ack
            segment_sent_time = time.time()
            while IS_WAITING_FOR_ACK:
                if CURRENT_UNACKNOWLEDGED_SEGMENTS >= MAX_UNACKNOWLEDGED_SEGMENTS:
                    # print("Server is not responding... closing connection")
                    CLIENT_TIMED_OUT = True
                    COMMUNICATION_TERMINATED = True
                    break
                if time.time() - segment_sent_time >= SEGMENT_RESEND_INTERVAL:
                    print("Resending text message...")
                    self.send_message_file_format(CURRENT_CATEGORY, [P], i + 1, fragments[i])
                    CURRENT_UNACKNOWLEDGED_SEGMENTS += 1
                    segment_sent_time = time.time()
                # time.sleep(1)

                self.receive()
            current_fragment_number += 1

        self.send_message(CURRENT_CATEGORY, [C], current_fragment_number,
                            'End of transmission')  # sending message about complete stream

    def terminate_communication(self):
        global COMMUNICATION_TERMINATED
        print("Would you like to terminate communication? (y/n):")
        terminate = input("Your choice:")
        if terminate == "y":
            self.send_message("1", [F], 1, 'Fin')
            # data = client.receive()
            # if "A" in segment.get_flags(format(data[1], "08b")) and "F" in segment.get_flags(format(data[1], "08b")):
            #     print("Received acknowledge to end of communication")
            #     COMMUNICATION_TERMINATED = True
            return True
        elif terminate == "n":
            return False

    # QUIT
    def quit(self):
        self.socket.close()
        # self.keep_alive_thread.join()
        print("Client closed...")
        sys.exit()


def system_message():
    print("What type of system message would you like to send?:")
    print("1 -> Switch roles")
    print("2 -> Go back to main menu")
    system_message = input("Your choice:")
    if system_message == "1":
        return '1'
    else:
        # CURRENT_CATEGORY = ''
        return '2'


def start_client(server_ip, server_port):
    global COMMUNICATION_STARTED, CURRENT_CATEGORY, IS_WAITING_FOR_ACK, CURRENT_UNACKNOWLEDGED_SEGMENTS, SWAP_ROLES, CLIENT_TIMED_OUT, COMMUNICATION_TERMINATED
    # print("To setup client, please enter the following information: ")

    # client_ip = input(" - Client IP: ")
    # client_port = int(input(" - Client Port: "))
    # server_ip = input(" - Server IP: ")
    # server_port = int(input(" - Server Port: "))

    # client_ip = "127.0.0.1"
    # client_port = 6061
    # server_ip = "127.0.0.1"
    # server_port = 6060

    client = Client(server_ip, server_port)
    client.start_keep_alive()
    data = "empty"

    while not COMMUNICATION_TERMINATED and not CLIENT_TIMED_OUT and not SWAP_ROLES:

        # establish communication with server and wait for server to send back syn ack. If syn ack is not received in 5 seconds, resend syn
        if not COMMUNICATION_STARTED:
            client.send_message("1", [S], 1, '')
            IS_WAITING_FOR_ACK = True
            print("Sending start of communication message")
            while not COMMUNICATION_STARTED:

                # # todo add resending if connect msg
                # if data == None:
                #     continue

                # waiting for ack
                segment_sent_time = time.time()
                while IS_WAITING_FOR_ACK:
                    client.receive()
                    if time.time() - segment_sent_time >= SEGMENT_RESEND_INTERVAL:
                        print("Resending text message...")
                        client.send_message("1", [S], 1, '')
                        segment_sent_time = time.time()
                    continue

        else:
            # while user does not input a valid category request for a valid category
            while CURRENT_CATEGORY != "1" and CURRENT_CATEGORY != "2" and CURRENT_CATEGORY != "3" and CURRENT_CATEGORY != "4" and not CLIENT_TIMED_OUT and not COMMUNICATION_TERMINATED:
                print("What type of message would you like to send? (text, file)?:")
                print("1 -> System message")
                print("2 -> Text message")
                print("3 -> File message")
                print("4 -> Terminate communication")
                CURRENT_CATEGORY = input("Your choice: ")

            if CLIENT_TIMED_OUT or COMMUNICATION_TERMINATED or SWAP_ROLES:
                break

            if CURRENT_CATEGORY == "4":
                if client.terminate_communication():
                    break

            # if user wants to send a system message
            if CURRENT_CATEGORY == "1":
                type_of_message = system_message()
                if type_of_message == "1":  # switch roles
                    client.send_message(CURRENT_CATEGORY, [W], 1, 'Switch roles')
                    client.receive()
                    CURRENT_CATEGORY = ''
                    # client.quit()
                elif type_of_message == "2":
                    CURRENT_CATEGORY = ''
                    continue

            # if user wants to send a text message
            elif CURRENT_CATEGORY == "2":
                client.send_text_message()
                CURRENT_CATEGORY = ''

            # if user wants to send a file message
            elif CURRENT_CATEGORY == "3":
                client.send_file_message()
                CURRENT_CATEGORY = ''
    return


if __name__ == "__main__":
    start_client(handler.SERVER_IP, handler.SERVER_PORT)
