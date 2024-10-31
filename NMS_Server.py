import socket
import struct
import json
from Message import Mensagem

def start_server_udp():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    LOCAL_ADR = "10.0.5.10"
    server_socket.bind((LOCAL_ADR, 8080))

    print("Servidor esperando por conexões...")

    while True:
        msg, client_address = server_socket.recvfrom(1024)
        if not msg:
            break
        
        print(f"Mensagem recebida de {client_address}")

        # Desserializar a mensagem recebida
        try:
            sequencia, identificador, dados = Mensagem.desserialize_udp(msg)
            print(f"Dados desserializados - Sequência: {sequencia}, Identificador: {identificador}, Dados: {dados.decode('utf-8')}")

            # Enviar um ACK de volta para o cliente
            ack_message = struct.pack('!I H', sequencia, identificador)
            server_socket.sendto(ack_message, client_address)
            print("ACK enviado para o cliente.")
        
        except struct.error as e:
            print("Erro ao desserializar a mensagem:", e)

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

a = int(input("0 - TCP , 1 - UDP :\n"))

if not a : 
    start_server_tcp()
else : start_server_udp()
