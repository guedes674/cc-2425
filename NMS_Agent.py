import socket
import json
from NetTask import UDP

def connect_udp():
    while True:
        a = input("Mensagem: ")
        
        # Criar a mensagem com protocolo, tipo, dados, identificador e sequência
        message = UDP("tipo", a, identificador=1, sequencia=1234)
        
        # Usar o método enviar_com_ack para enviar a mensagem com controle de fluxo e ACK
        ack_recebido = message.enviar_com_ack('10.0.5.10', 8080)

        # Confirmação do envio
        if ack_recebido:
            print("ACK recebido.")
        else:
            print("Falha ao enviar a mensagem após múltiplas tentativas.")


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

b = int(input("0 - TCP , 1 - UDP :\n"))

if not b : 
    connect_tcp()
else : connect_udp()