import socket

CLIENT_IP = "127.0.0.1"
CLIENT_PORT = 50602

SERVER_IP = "127.0.0.1"
SERVER_PORT = 50601


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
        return data.decode("utf-8")

    def send_message(self, message):
        self.socket.sendto(bytes(message, "utf-8"), (self.server_ip, self.server_port))

    def quit(self):
        self.socket.close()
        print("Client closed...")


if __name__ == "__main__":
    client = Client(CLIENT_IP, CLIENT_PORT, SERVER_IP, SERVER_PORT)
    data = "empty"

    while data != "End connection message recieved... closing connection":
        print("Input your message: ")
        client.send_message(input())
        data = client.receive()
        print(data)

    client.quit()