import socket
import struct
import threading
import time
import os
import zlib

import segment


SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601

COMMUNICATION_STARTED = False

KEEP_ALIVE_TIMEOUT = 10  # seconds TODO change in the future!
KEEP_ALIVE_MESSAGE = struct.pack("!B", 0x06)

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
FULL_TEXT_MESSAGE = ""

GETTING_FILE_MESSAGE = False


class Server:
    def __init__(self, ip, port) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket creation
        self.socket.bind((ip, port))  # needs to be a tuple

        # KEPP ALIVE
        self.client_last_seen = time.time()
        self.timeout_thread = threading.Thread(target=self.check_keep_alive_continuously)
        self.timeout_thread.daemon = True
        self.timeout_thread.start()

    def receive(self):
        data = None
        while data == None:
            data, self.client = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            # self.client_last_keep_alive = time.time()


        # print("Recieved message: ", data)
        # # return str(data, encoding="utf-8")
        # print("type: ", type(data[0]))  # integer
        # print("data size:", len(data))
        # print("Category: ", data[0])
        # print("Flags raw: ", data[1])
        # print("Flags in binary form: ", format(data[1], "08b"))
        # print("Flags: ", self.get_flags(format(data[1], "08b")))
        # print("Message: ", data[2::].decode("utf-8"))
        self.client_last_seen = time.time()
        return data

    # def send_message(self, category, flags, message):
    #
    #     checksum = segment.creating_checksum(message)
    #     message = segment.creating_category(category) + segment.creating_flags(flags) + segment.creating_fragment_number(1) + checksum + message.encode("utf-8")
    #
    #     self.socket.sendto(message,  self.client)

    def check_keep_alive_continuously(self):
        while True:
            time.sleep(1.5)  # Adjust the sleep interval as needed
            self.check_keep_alive_timer()

    def check_keep_alive_timer(self):
        current_time = time.time()
        # print("Hasn't received msg in: ", current_time - self.client_last_seen)
        if current_time - self.client_last_seen > KEEP_ALIVE_TIMEOUT:
            print("Client has timed out... closing connection")
            self.quit()

    def listen_to_communication_start(self, data):
        global COMMUNICATION_STARTED
        if data[0] == 1:
            if "S" in segment.get_flags(format(data[1], "08b")):
                print("Recieved start of communication")
                COMMUNICATION_STARTED = True
                self.send_response()

    def listening_text_message(self, data):
        global GETTING_TEXT_MESSAGE
        if data[0] == 2:  # category is correct
            if "N" in segment.get_flags(format(data[1], "08b")):  # flags is start of text message
                print("Recieved start of text message")
                GETTING_TEXT_MESSAGE = True
        # print("Text message: ", data)

    def receiving_text_message(self, data):
        global FULL_TEXT_MESSAGE
        if data[0] == 2:
            if "P" in segment.get_flags(format(data[1], "08b")):  # flag is text message
                print("Recieved text message")
                FULL_TEXT_MESSAGE += data[8::].decode("utf-8")

    def receiving_end_of_text_message(self, data):
        global FULL_TEXT_MESSAGE, GETTING_TEXT_MESSAGE
        if data[0] == 2:
            if "C" in segment.get_flags(format(data[1], "08b")):  # flag is end of text message
                print("Recieved end of text message")
                GETTING_TEXT_MESSAGE = False
                print("Full text message: ", FULL_TEXT_MESSAGE)
                FULL_TEXT_MESSAGE = ""

    def send_response(self):
        self.socket.sendto(b"Message recieved...", self.client)

    def send_last_response(self):
        self.socket.sendto(b"End connection message recieved... closing connection", self.client)

    def quit(self):
        self.socket.close()
        print("Server closed...")


def waiting_for_connection_establishment():
    global data, COMMUNICATION_STARTED
    print("Waiting for start of communication message...")
    while not COMMUNICATION_STARTED:
        data = server.receive()
        if "S" in segment.get_flags(format(data[1], "08b")):
            print("Received start of communication message, sending response...")

            # send response
            message = segment.creating_category('1') + segment.creating_flags(
                [S, A]) + segment.creating_fragment_number(1) + segment.creating_checksum('') + ''.encode("utf-8")
            server.socket.sendto(message, server.client)

            COMMUNICATION_STARTED = True
            continue


def is_keep_alive_msg(data):
    if data[0] == 1:
        if "K" in segment.get_flags(format(data[1], "08b")):
            # print("Recieved keep alive message")
            return True
    return False


if __name__ == "__main__":
    server = Server(SERVER_IP, SERVER_PORT)
    # server.start_keep_alive_monitor_thread()
    data = "empty"


    while data != "End connection":
        # global COMMUNICATION_STARTED, CURRENT_CATEGORY
        # TODO need to tidy up this code
        # establish communication with server and wait for server to send back syn ack. If syn ack is not received in 5 seconds, resend syn
        if not COMMUNICATION_STARTED:
            waiting_for_connection_establishment()
        else:
            if data != "empty":
                server.send_response()

            data = server.receive()

            # server.check_keep_alive(data) # check if client has timed out

            # Check checksum before processing segment
            if segment.check_checksum(data):
                if is_keep_alive_msg(data):
                    message = segment.creating_category('1') + segment.creating_flags(
                        [K, A]) + segment.creating_fragment_number(1) + segment.creating_checksum('Keep Alive') + 'Keep Alive'.encode(
                        "utf-8")
                    server.socket.sendto(message, server.client)
                    # print("Received keep alive message")
                    continue
                if not GETTING_TEXT_MESSAGE:
                    server.listening_text_message(data)
                elif GETTING_TEXT_MESSAGE:
                    server.receiving_text_message(data)
                    server.receiving_end_of_text_message(data)
            else:
                print("Checksums do not match")
                # TODO add what to do if checksums do not match (most likely ignore and wait next message)

    server.send_last_response()
    server.quit()
