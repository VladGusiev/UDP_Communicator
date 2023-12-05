import socket
import struct
import threading
import time
import os
import zlib
import sys
import keyboard

import segment
import handler

COMMUNICATION_STARTED = False
COMMUNICATION_TERMINATED = False

KEEP_ALIVE_TIMEOUT = 15  # seconds
SERVER_TIMED_OUT = False

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

CATEGORIES = {
    1: "System",
    2: "Text",
    3: "File"
}

GETTING_TEXT_MESSAGE = False
FULL_TEXT_MESSAGE = []

GETTING_FILE_MESSAGE = False
FULL_FILE_MESSAGE = []

FILE_PATH = "."  # by default pycharm will save files in the same directory as the project
FILE_NAME = ""

SWAP_ROLES = False

ALL_FILES_RECEIVED = []


class Server:
    def __init__(self, ip, port) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

        # KEPP ALIVE
        self.client_last_seen = time.time()
        self.timeout_thread = threading.Thread(target=self.check_keep_alive_continuously)
        self.timeout_thread.daemon = True
        self.timeout_thread.start()

        # check user input to change directory, where to store files
        self.user_input = threading.Thread(target=self.check_user_input_continuously)
        self.user_input.daemon = True
        self.user_input.start()

    def receive(self):
        data = None
        try:
            while data is None:
                data, self.client = self.socket.recvfrom(1472)  # buffer size is 1024 bytes
            self.client_last_seen = time.time()

            segment.CLIENT_INFO = tuple()
            segment.CLIENT_INFO = self.client

            return data
        except socket.error:
            ...

    def check_user_input_continuously(self):
        while not COMMUNICATION_TERMINATED and not SERVER_TIMED_OUT:
            self.check_user_input()

    def check_user_input(self):
        global FILE_PATH, COMMUNICATION_TERMINATED, SERVER_TIMED_OUT
        if COMMUNICATION_TERMINATED or SERVER_TIMED_OUT:
            return
        is_pressed = False
        try:
            if keyboard.is_pressed('['):
                print("Current save location: ", FILE_PATH, "\n")
            elif keyboard.is_pressed(']'):
                FILE_PATH = input("\nEnter new save location: ")
                while not os.path.exists(FILE_PATH):
                    FILE_PATH = input("\nEnter new save location: ")
                print("Save location changed to: ", FILE_PATH, "\n")
            elif keyboard.is_pressed(';'):
                # send swap roles message
                print("Sending swap roles message...")
                message = segment.creating_category('1') + segment.creating_flags(
                    [W]) + segment.creating_fragment_number(1) + segment.creating_checksum('Swap roles') + 'Swap roles'.encode("utf-8")
                self.socket.sendto(message, self.client)
                # return
            elif keyboard.is_pressed("/"):
                print("\nAll received files: ", ALL_FILES_RECEIVED)
        except:
            ...

    def check_keep_alive_continuously(self):
        global COMMUNICATION_TERMINATED, SERVER_TIMED_OUT, SWAP_ROLES
        while not COMMUNICATION_TERMINATED and not SERVER_TIMED_OUT:
            time.sleep(1)
            self.check_keep_alive_timer()

    def check_keep_alive_timer(self):
        global COMMUNICATION_TERMINATED, COMMUNICATION_STARTED, SERVER_TIMED_OUT, SWAP_ROLES

        current_time = time.time()
        if current_time - self.client_last_seen > KEEP_ALIVE_TIMEOUT:
            print("Client has timed out... closing connection")
            SERVER_TIMED_OUT = True
            COMMUNICATION_TERMINATED = True
            self.quit()
            return

    def listening_text_message(self, data):
        global GETTING_TEXT_MESSAGE
        if data[0] == 2:
            if "N" in segment.get_flags(format(data[1], "08b")):  # flags is start of text message
                print("Received start of text message")
                GETTING_TEXT_MESSAGE = True

    def receiving_text_message(self, data):
        global FULL_TEXT_MESSAGE
        if data[0] == 2:
            if "P" in segment.get_flags(format(data[1], "08b")):  # flag is text message
                print("Received text message")

                text_answer = segment.creating_category('2') + segment.creating_flags(
                    [P, A]) + segment.creating_fragment_number(1) + segment.creating_checksum(
                    'Text Message Received') + 'Text Message Received'.encode("utf-8")
                self.socket.sendto(text_answer, self.client)

                full_string = data[8::].decode("utf-8")
                text_message = full_string.split("***")

                for message in FULL_TEXT_MESSAGE:
                    if data[2:4] == message[1]:
                        print("Duplicate message")
                        return
                FULL_TEXT_MESSAGE.append([text_message[0], data[2:4]])

    def receiving_end_of_text_message(self, data):
        global FULL_TEXT_MESSAGE, GETTING_TEXT_MESSAGE
        if data[0] == 2:
            if "C" in segment.get_flags(format(data[1], "08b")):  # flag is end of text message
                print("Received end of text message")
                GETTING_TEXT_MESSAGE = False
                full_string = ""

                for message in FULL_TEXT_MESSAGE:
                    full_string += message[0]
                print("Full text message: ", full_string)

                FULL_TEXT_MESSAGE = []

                ALL_FILES_RECEIVED.append(["Full string: " + full_string, "Size of message: " + str(len(full_string)), "Fragments number: " + str(int.from_bytes(data[2:4], byteorder='big')-1)])

    def listening_file_message(self, data):
        global GETTING_FILE_MESSAGE, FILE_NAME
        if data[0] == 3:
            if "N" in segment.get_flags(format(data[1], "08b")):
                print("Received start of file message")
                GETTING_FILE_MESSAGE = True
                FILE_NAME = data[8::].decode("utf-8")

    # method to receive file messages from client
    def receiving_file_message(self, data):
        global FULL_FILE_MESSAGE
        if data[0] == 3:
            if "P" in segment.get_flags(format(data[1], "08b")):
                print("Recieved file message")

                file_answer = segment.creating_category('3') + segment.creating_flags(
                    [P, A]) + segment.creating_fragment_number(1) + segment.creating_checksum(
                    'File Message Received') + 'File Message Received'.encode("utf-8")
                self.socket.sendto(file_answer, self.client)

                # print("File message: ", data[8::])
                # print("Fragment number: ", data[2:4])

                # check if message is duplicate
                for message in FULL_FILE_MESSAGE:
                    if data[2:4] == message[1]:
                        print("Duplicate message")
                        return
                FULL_FILE_MESSAGE.append([data[8::], data[2:4]])

    # receive end of file message from client and save file to specified location
    def receiving_end_of_file_message(self, data):
        global FULL_FILE_MESSAGE, GETTING_FILE_MESSAGE, FILE_NAME, FILE_PATH
        if data[0] == 3:
            if "C" in segment.get_flags(format(data[1], "08b")):
                print("Recieved end of file message")
                GETTING_FILE_MESSAGE = False

                f_write = open(FILE_PATH + '\\' + FILE_NAME, "wb")
                for packet in FULL_FILE_MESSAGE:
                    f_write.write(packet[0])
                f_write.close()

                FULL_FILE_MESSAGE = []

                ALL_FILES_RECEIVED.append(["Full path: " + FILE_PATH + '\\' + FILE_NAME, "Size of file: " + str(os.path.getsize(FILE_PATH + '\\' + FILE_NAME)), "Fragments number: " + str(int.from_bytes(data[2:4], byteorder='big')-1)])


    def quit(self):
        self.socket.close()
        self.user_input.join()
        print("\nServer closed...")

    def terminate_communication(self):
        global COMMUNICATION_TERMINATED
        print("Received communication termination message... closing connection")
        message = segment.creating_category('1') + segment.creating_flags(
            [F, A]) + segment.creating_fragment_number(1) + segment.creating_checksum(
            'Fin') + 'Fin'.encode("utf-8")
        self.socket.sendto(message, self.client)
        COMMUNICATION_TERMINATED = True

    def waiting_for_connection_establishment(self):
        global data, COMMUNICATION_STARTED
        print("Waiting for start of communication message...")
        while not COMMUNICATION_STARTED:
            data = self.receive()

            if data is None:
                break

            if "S" in segment.get_flags(format(data[1], "08b")):
                print("Received start of communication message, sending response...")

                # send response
                message = segment.creating_category('1') + segment.creating_flags(
                    [S, A]) + segment.creating_fragment_number(1) + segment.creating_checksum('') + ''.encode("utf-8")
                self.socket.sendto(message, self.client)

                COMMUNICATION_STARTED = True
                continue

    def swap_roles(self):
        global COMMUNICATION_STARTED, COMMUNICATION_TERMINATED, SWAP_ROLES, FILE_PATH, FILE_NAME
        print("Received swap roles message... swapping roles")

        # send response
        message = segment.creating_category('1') + segment.creating_flags(
            [W, A]) + segment.creating_fragment_number(1) + segment.creating_checksum('Switch roles acknowledge') + 'Switch roles acknowledge'.encode("utf-8")
        self.socket.sendto(message, self.client)

        COMMUNICATION_STARTED = False
        COMMUNICATION_TERMINATED = False
        SWAP_ROLES = True
        FILE_PATH = "."
        FILE_NAME = ""

    def swap_roles2(self):
        global COMMUNICATION_STARTED, COMMUNICATION_TERMINATED, SWAP_ROLES, FILE_PATH, FILE_NAME
        print("Received swap roles message... swapping roles")

        COMMUNICATION_STARTED = False
        COMMUNICATION_TERMINATED = False
        SWAP_ROLES = True
        FILE_PATH = "."
        FILE_NAME = ""


def is_keep_alive_msg(data):
    if data[0] == 1:
        if "K" in segment.get_flags(format(data[1], "08b")):
            return True
    return False


def is_termination_msg(data):
    if data[0] == 1:
        if "F" in segment.get_flags(format(data[1], "08b")):
            return True
    return False


def is_swap_roles_msg(data):
    if data[0] == 1:
        if "W" in segment.get_flags(format(data[1], "08b")):
            return True
    return False


def is_confirming_swap_roles_msg(data):
    if data[0] == 1:
        if "W" in segment.get_flags(format(data[1], "08b")) and "A" in segment.get_flags(format(data[1], "08b")):
            return True
    return False


def start_server(server_ip, server_port):
    print("List of commands accessible for server: \n>> [ - to see current save location \n>> ] - to change save location \n>> ; - to swap roles \n>> / - to see all received files \n")
    print("!Note: Program is listening to key events, the loger you press the key, the more times it will be executed!\n")
    data = "empty"

    server = Server(server_ip, server_port)
    print("After end of communication, due to timeout or termination or swap, type anything to close server...")
    while not COMMUNICATION_TERMINATED and not SERVER_TIMED_OUT:

        # establish communication with server and wait for server to send back syn ack.
        if not COMMUNICATION_STARTED:
            server.waiting_for_connection_establishment()
        else:
            data = server.receive()

            if data is None:
                continue

            if is_termination_msg(data):
                server.terminate_communication()
                break

            if is_swap_roles_msg(data):
                server.swap_roles()
                break

            if is_confirming_swap_roles_msg(data):
                server.swap_roles2()
                break

            # Check checksum before processing segment
            if segment.check_checksum(data):
                if is_keep_alive_msg(data):
                    message = segment.creating_category('1') + segment.creating_flags(
                        [K, A]) + segment.creating_fragment_number(1) + segment.creating_checksum('Keep Alive') + 'Keep Alive'.encode(
                        "utf-8")
                    server.socket.sendto(message, server.client)
                    continue
                if not GETTING_TEXT_MESSAGE:
                    server.listening_text_message(data)
                elif GETTING_TEXT_MESSAGE:
                    server.receiving_text_message(data)
                    server.receiving_end_of_text_message(data)

                if not GETTING_FILE_MESSAGE:
                    server.listening_file_message(data)
                elif GETTING_FILE_MESSAGE:
                    server.receiving_file_message(data)
                    server.receiving_end_of_file_message(data)

            else:
                print("Checksums do not match")
    server.quit()


if __name__ == "__main__":
    start_server(handler.SERVER_IP, handler.SERVER_PORT)
