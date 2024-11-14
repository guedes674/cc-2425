import socket
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

        print("Aguardando tarefas do NMS_Server...")
        while True:
            data, addr = sock.recvfrom(1024)
            sequencia, identificador, dados = UDP.desserialize(data)
            
            # Processar a tarefa recebida (exemplo de tratamento de mensagens)
            if identificador == self.identificador:
                print(f"Tarefa recebida: {dados.decode('utf-8')}")

    # Implementar outras funções para coleta de métricas, enviar alertas, etc., conforme necessário

# Exemplo de uso
nms_agent = NMS_Agent(server_endereco="10.0.5.10", server_porta=5000)
nms_agent.connect_to_server()
nms_agent.receive_task()
