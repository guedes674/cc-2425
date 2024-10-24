import socket
import struct
import json

def start_server_udp():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    LOCAL_ADR = "10.0.5.10"
    server_socket.bind((LOCAL_ADR, 8080))

    print("Servidor esperando por conexões...")

    while True:
        msg, clientAdress = server_socket.recvfrom(1024)
        print(clientAdress)
        if not msg:
            break
        print(f"Recebido: {msg.decode()}")

def start_server_tcp():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    LOCAL_ADR = "10.0.5.10"
    server_socket.bind((LOCAL_ADR, 8080))
    server_socket.listen(1)

    print("Servidor esperando por conexões...")
    conn, addr = server_socket.accept()
    print(f"Conectado por {addr}")

    while True:
        msg = conn.recv(1024)
        if not msg:
            break
        decoded_json = msg.decode('utf-8')
        try:
            parsed_json = json.loads(decoded_json)
            print(type(parsed_json))
            print(f"Recebido: {parsed_json}")
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
        conn.sendall(msg)   
    conn.close()

a = input("0 - TCP , 1 - UDP :\n")

if a : 
    start_server_tcp()
else : start_server_udp()
