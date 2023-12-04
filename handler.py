import client
import server
import segment
import socket

# handler is the main entry point for the application and is responsible for starting the client and server
# processes. It also handles the communication between the client and server processes.

CURRENT_ROLE = ''

SERVER_IP = ''
SERVER_PORT = 0


def main():
    global CURRENT_ROLE, SERVER_IP, SERVER_PORT, CLIENT_IP, CLIENT_PORT, CLIENT_INFO
    print("Choose your, role (c - client/ s - server): ")
    CURRENT_ROLE = input(">> ")
    while CURRENT_ROLE != "c" and CURRENT_ROLE != "s":
        print("Invalid role")
        print("Choose your, role (c - client/ s - server): ")
        CURRENT_ROLE = input(">> ")
    if CURRENT_ROLE == "c":
        request_ip_and_port()
        client.start_client(SERVER_IP, SERVER_PORT)
    elif CURRENT_ROLE == "s":
        request_ip_and_port()
        server.start_server(SERVER_IP, SERVER_PORT)

    while client.SWAP_ROLES or server.SWAP_ROLES:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)
        # print("Client info: ", segment.CLIENT_INFO)
        reset_all()
        if CURRENT_ROLE == "c":
            CURRENT_ROLE = "s"
            server.start_server(host_ip, SERVER_PORT)
        elif CURRENT_ROLE == "s":
            CURRENT_ROLE = "c"
            client.start_client(segment.CLIENT_INFO[0], SERVER_PORT)

def request_ip_and_port():
    global SERVER_IP, SERVER_PORT
    while SERVER_IP == '' or SERVER_PORT == 0:
        print("Enter server ip: ")
        SERVER_IP = input(">> ")
        print("Enter server port: ")
        SERVER_PORT = input(">> ")
        try:
            SERVER_PORT = int(SERVER_PORT)
        except ValueError:
            print("Invalid port")
            SERVER_PORT = 0

def reset_all():
    client.SWAP_ROLES = False
    client.COMMUNICATION_STARTED = False
    client.COMMUNICATION_TERMINATED = False
    client.CLIENT_TIMED_OUT = False
    client.IS_WAITING_FOR_ACK = False
    client.UNACKNOWLEDGED_KEEP_LIVE = 0

    server.SWAP_ROLES = False
    server.COMMUNICATION_STARTED = False
    server.COMMUNICATION_TERMINATED = False
    server.SERVER_TIMED_OUT = False
    server.FILE_PATH = "."  # by default pycharm will save files in the same directory as the project
    server.FILE_NAME = ""
    server.ALL_FILES_RECEIVED = []

if __name__ == "__main__":
    main()
