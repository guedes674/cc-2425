import socket
import json
import subprocess
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

def ping(host, num):
    try:
        command = ['ping', host]
        if num is not None:
            command += ['-c', str(num)]

        # Executa o comando e captura a saída
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError:
        print(f"Erro ao executar o ping")
        return None

def iperf(host, num):
    try:
        command = ['iperf', '-c', host]
        if num is not None:
            command += ['-t', str(num)]

        # Executa o comando e captura a saída
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError:
        print(f"Erro ao executar o iperf")
        return None

b = int(input("0 - TCP , 1 - UDP :\n"))

if not b : 
    connect_tcp()
else : connect_udp()