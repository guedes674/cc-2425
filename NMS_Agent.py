import socket
import json
def connect_udp():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while (True):
        
        a = input("Message : ")
        message = {
            "Message" : a,
            "Address" : "Ola"
        }
        server_socket.sendto(bytes(message,encoding='utf-8'),('10.0.5.10', 8080))

def connect_tcp():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('10.0.5.10', 8080))
    while (True):
        a = input("Message : ")
        message = {
            "Message" : a,
            "Address" : "Ola"
        }
        json_message = json.dumps(message)
        server_socket.sendall(bytes(str(json_message),encoding='utf-8'))

b = input("0 - TCP , 1 - UDP :\n")

if b : 
    connect_tcp()
else : connect_udp()