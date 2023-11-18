import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601


class Server:
    def __init__(self, ip, port) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket creation
        self.socket.bind((ip, port)) # needs to be a tuple

    def receive(self):
        data = None
        while data == None:
            data, self.client = self.socket.recvfrom(1024)  # buffer size is 1024 bytes
        print("Recieved message: ", data)
        # return data
        return data.decode("utf-8")

    def send_response(self):
        self.socket.sendto(b"Message recieved...", self.client)

    def send_last_response(self):
        self.socket.sendto(b"End connection message recieved... closing connection", self.client)

    def quit(self):
        self.socket.close()
        print("Server closed...")

if __name__ == "__main__":
    server = Server(SERVER_IP, SERVER_PORT)
    data = "empty"

    while data != "End connection":
        if data != "empty":
            server.send_response()
        data = server.receive()

    server.send_last_response()
    server.quit()