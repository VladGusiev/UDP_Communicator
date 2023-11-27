import socket
import struct
import threading
import time
import os
import zlib


SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601

KEEP_ALIVE_TIMEOUT = 20  # seconds
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

        self.client_last_keep_alive = time.time()

    def receive(self):
        data = None
        while data == None:
            data, self.client = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
            # self.client_last_keep_alive = time.time()

        if self.check_checksum(data):
            if not GETTING_TEXT_MESSAGE:
                server.listening_text_message(data)
            elif GETTING_TEXT_MESSAGE:
                server.receiving_text_message(data)
                server.receiving_end_of_text_message(data)
        else:
            print("Checksums do not match")
            # TODO add what to do if checksums do not match (most likely ignore and wait next message)


        # print("Recieved message: ", data)
        # # return str(data, encoding="utf-8")
        # print("type: ", type(data[0]))  # integer
        # print("data size:", len(data))
        # print("Category: ", data[0])
        # print("Flags raw: ", data[1])
        # print("Flags in binary form: ", format(data[1], "08b"))
        # print("Flags: ", self.get_flags(format(data[1], "08b")))
        # print("Message: ", data[2::].decode("utf-8"))
        return data


    def listen_to_communication_start(self, data):
        global COMMUNICATION_STARTED
        if data[0] == 1:
            if "S" in self.get_flags(format(data[1], "08b")):
                print("Recieved start of communication")
                COMMUNICATION_STARTED = True
                self.send_response()
    def creating_checksum(self, message):
        checksum = zlib.crc32(bytes(message, "utf-8"))
        checksum = struct.pack("!I", checksum)
        return checksum

    def check_checksum(self, data):
        checksum = data[4:8]
        message = data[8::].decode("utf-8")
        calculated_checksum = self.creating_checksum(message)
        if checksum == calculated_checksum:
            return True
        else:
            return False

    def get_flags(self, flags):
        all_flags = []
        i = 1
        for f in flags:
            if f == "1":
                all_flags.append(FLAGS[i])
            i += 1
        return all_flags

    def listening_text_message(self, data):
        global GETTING_TEXT_MESSAGE
        if data[0] == 2:  # category is correct
            if "N" in self.get_flags(format(data[1], "08b")):  # flags is start of text message
                print("Recieved start of text message")
                GETTING_TEXT_MESSAGE = True
        # print("Text message: ", data)

    def receiving_text_message(self, data):
        global FULL_TEXT_MESSAGE
        if data[0] == 2:
            if "P" in self.get_flags(format(data[1], "08b")):  # flag is text message
                print("Recieved text message")
                FULL_TEXT_MESSAGE += data[8::].decode("utf-8")

    def receiving_end_of_text_message(self, data):
        global FULL_TEXT_MESSAGE, GETTING_TEXT_MESSAGE
        if data[0] == 2:
            if "C" in self.get_flags(format(data[1], "08b")):  # flag is end of text message
                print("Recieved end of text message")
                GETTING_TEXT_MESSAGE = False
                print("Full text message: ", FULL_TEXT_MESSAGE)
                FULL_TEXT_MESSAGE = ""

    def send_response(self):
        self.socket.sendto(b"Message recieved...", self.client)

    def send_last_response(self):
        self.socket.sendto(b"End connection message recieved... closing connection", self.client)

    # # KEEP ALIVE MONITOR
    # def keep_alive_monitor(self):
    #     while True:
    #         time.sleep(1)
    #         current_time = time.time()
    #         if current_time - self.client_last_keep_alive > KEEP_ALIVE_TIMEOUT:
    #             print("Client timed out. Closing connection.")
    #             self.quit()
    #             break
    #
    # def start_keep_alive_monitor_thread(self):
    #     keep_alive_thread = threading.Thread(target=self.keep_alive_monitor)
    #     keep_alive_thread.start()

    def quit(self):
        self.socket.close()
        print("Server closed...")


if __name__ == "__main__":
    server = Server(SERVER_IP, SERVER_PORT)
    # server.start_keep_alive_monitor_thread()
    data = "empty"

    while data != "End connection":
        if data != "empty":
            server.send_response()

        data = server.receive()


    server.send_last_response()
    server.quit()