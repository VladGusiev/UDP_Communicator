import client
import server

# handler is the main entry point for the application and is responsible for starting the client and server
# processes. It also handles the communication between the client and server processes.

CURRENT_ROLE = ''


def main():
    global CURRENT_ROLE
    print("Choose your, role (c - client/ s - server): ")
    CURRENT_ROLE = input(">> ")
    while CURRENT_ROLE != "c" and CURRENT_ROLE != "s":
        print("Invalid role")
        print("Choose your, role (c - client/ s - server): ")
        CURRENT_ROLE = input(">> ")
    if CURRENT_ROLE == "c":
       client.start_client()
    elif CURRENT_ROLE == "s":
        server.start_server()

    while client.SWAP_ROLES or server.SWAP_ROLES:
        reset_all()
        if CURRENT_ROLE == "c":


            CURRENT_ROLE = "s"
            server.start_server()
        elif CURRENT_ROLE == "s":

            CURRENT_ROLE = "c"
            client.start_client()
        #
        # if client.SWAP_ROLES:
        #     client.SWAP_ROLES = False
        #     CURRENT_ROLE = "s"
        #     server.start_server()
        # elif server.SWAP_ROLES:
        #     server.SWAP_ROLES = False
        #     CURRENT_ROLE = "c"
        #     client.start_client()

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

if __name__ == "__main__":
    main()
