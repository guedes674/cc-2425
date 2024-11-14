import socket
<<<<<<< HEAD
import json
import subprocess
=======
>>>>>>> 5b2678b24590fff552d86b2947f614b8e29ae3d1
from NetTask import UDP

class NMS_Agent:
    def __init__(self, server_endereco, server_porta):
        self.id = self.get_device_address()    # Obter o endereço IP do prórprio nodo
        self.server_endereco = server_endereco
        self.server_porta = server_porta

    # Obtém o endereço IP local do dispositivo (ID do NMS_Agent)
    def get_device_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Não é necessário que o endereço 8.8.8.8 esteja acessível, é apenas para obter o IP
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
        except Exception:
            ip_address = "127.0.0.1" 
        finally:
            s.close()
        return ip_address

    # Usando a função registo do NetTask para registrar o NMS_Agent
    def connect_to_server(self):
        mensagem_registo = UDP(tipo=1, dados="", identificador=self.id, sequencia=1)
        mensagem_registo.registo(self.server_endereco, self.server_porta)

    # por ver
    def receive_task(self):
        # Função para ouvir e desserializar tarefas do servidor
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 0))  # Liga o socket a qualquer porta disponível para receber dados

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

    # Implementar outras funções para coleta de métricas, enviar alertas, etc., conforme necessário

# Exemplo de uso
nms_agent = NMS_Agent(server_endereco="10.0.5.10", server_porta=5000)
nms_agent.connect_to_server()
nms_agent.receive_task()
