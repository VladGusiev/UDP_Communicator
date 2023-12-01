import socket
import threading
import time
import struct
import os
import zlib
import sys

import segment

# CLIENT_IP = "127.0.0.1"
# CLIENT_PORT = 50602
#
# SERVER_IP = "127.0.0.1"
# SERVER_PORT = 50601

COMMUNICATION_STARTED = False
COMMUNICATION_TERMINATED = False

# for sending keep alive messages
KEEP_ALIVE_INTERVAL = 3  # seconds
UNACKNOWLEDGED_KEEP_LIVE = 0
MAX_UNACKNOWLEDGED_KEEP_LIVE = 5

# for resending packets that were not acknowledged
SEGMENT_RESEND_INTERVAL = 6 # seconds
IS_WAITING_FOR_ACK = False



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
        while not COMMUNICATION_TERMINATED:
            if UNACKNOWLEDGED_KEEP_LIVE >= 5:
                print("\nServer is not responding... closing connection")
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
        self.quit()

    def receive(self):
        global UNACKNOWLEDGED_KEEP_LIVE, COMMUNICATION_TERMINATED, IS_WAITING_FOR_ACK
        data = None
        try:
            while data == None:
                data, self.server = self.socket.recvfrom(1024)  # buffer size is 1024 bytes

            if IS_WAITING_FOR_ACK:
                if data[0] == 2:
                    if "A" in segment.get_flags(format(data[1], "08b")) and "P" in segment.get_flags(
                            format(data[1], "08b")):
                        IS_WAITING_FOR_ACK = False
                        print("Received ack for text message")
            # check if server sent back ack
            if data[0] == 1:
                if "A" in segment.get_flags(format(data[1], "08b")) and "K" in segment.get_flags(
                        format(data[1], "08b")):
                    # print("Recieved keep alive ack")
                    UNACKNOWLEDGED_KEEP_LIVE = 0
                    # print("UNACKNOWLEDGED_KEEP_LIVE: ", UNACKNOWLEDGED_KEEP_LIVE)

                if "A" in segment.get_flags(format(data[1], "08b")) and "F" in segment.get_flags(format(data[1], "08b")):
                    print("Received acknowledge to end of communication")
                    COMMUNICATION_TERMINATED = True
                    self.quit()
            return data

        except socket.error:
            ...
            # print("Server is not responding... closing connection")
            # self.quit()

    # TODO add fragmenting, sending message about new stram and message about complete stream so server can reassemble
    def send_text_message(self):
        global CURRENT_CATEGORY, IS_WAITING_FOR_ACK

        current_fragment_number = 0
        fragment_size = input("Input fragment size: ")
        while not fragment_size.isdigit():
            print("Fragment size must be a number")
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
                if time.time() - segment_sent_time >= SEGMENT_RESEND_INTERVAL:
                    print("Resending text message...")
                    self.send_message(CURRENT_CATEGORY, [P], i+1, fragments[i])
                    segment_sent_time = time.time()
                time.sleep(1)

                self.receive()
            current_fragment_number += 1

        client.send_message(CURRENT_CATEGORY, [C], current_fragment_number,  'End of transmission')  # sending message about complete stream

    def send_message(self, category, flags, frag_num, message):

        checksum = segment.creating_checksum(message)
        message = segment.creating_category(category) + segment.creating_flags(flags) + segment.creating_fragment_number(frag_num) + checksum + message.encode("utf-8")

        self.socket.sendto(message, (self.server_ip, self.server_port))


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





# if send_text_message() == 'x':

# CURRENT_CATEGORY = ''
# continue


if __name__ == "__main__":

    print("To setup client, please enter the following information: ")

    # client_ip = input(" - Client IP: ")
    # client_port = int(input(" - Client Port: "))
    # server_ip = input(" - Server IP: ")
    # server_port = int(input(" - Server Port: "))

    client_ip = "127.0.0.1"
    client_port = 6061
    server_ip = "127.0.0.1"
    server_port = 6060

    client = Client(client_ip, client_port, server_ip, server_port)
    client.start_keep_alive()
    data = "empty"

    while not COMMUNICATION_TERMINATED:
        # global COMMUNICATION_STARTED, CURRENT_CATEGORY
        # establish communication with server and wait for server to send back syn ack. If syn ack is not received in 5 seconds, resend syn
        if not COMMUNICATION_STARTED:
            client.send_message("1", [S], 1, '')
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
                print("4 -> Terminate communication")
                CURRENT_CATEGORY = input("Your choice: ")
            if CURRENT_CATEGORY == "4":
                if client.terminate_communication():
                    break

            # if user wants to send a system message
            if CURRENT_CATEGORY == "1":
                type_of_message = system_message()
                if type_of_message == "1":  # switch roles
                    client.send_message(CURRENT_CATEGORY, [W], 1, '')
                    CURRENT_CATEGORY = ''
                    continue
                elif type_of_message == "2":
                    CURRENT_CATEGORY = ''
                    continue

            # if user wants to send a text message
            elif CURRENT_CATEGORY == "2":
                client.send_text_message()
                CURRENT_CATEGORY = ''

                # client.send_message(CURRENT_CATEGORY, [N], 'fragment size info will be here')  # sending message about new stream
                # if send_text_message() == 'x':
                    # client.send_message(CURRENT_CATEGORY, [C], '')  # sending message about complete stream
                    # CURRENT_CATEGORY = ''
                    # continue


        # TODO ADD FILE SENDING
        # print("Input your message: ")
        # client.send_message(CURRENT_CATEGORY, input())
        # data = client.receive()
        # print(data)

    # client.quit()