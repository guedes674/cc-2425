import socket, json
from NetTask import UDP

class NMS_Agent:
    def __init__(self, server_endereco, server_porta):
        self.id = self.get_device_address()    # Obter o endereço IP do prórprio nodo
        self.server_endereco = server_endereco
        self.server_porta = server_porta

        # Criar o socket UDP para comunicação com o servidor
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.id, 0))  # Liga o socket ao endereço IP do agente e a uma porta disponível


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

    # No método receive_task do agente
    def receive_task(self):
        print("[DEBUG - receive_task] Aguardando tarefas do NMS_Server...")
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                print(f"[DEBUG - receive_task] Mensagem recebida de {addr}")

                # Desserializar a mensagem recebida para extrair a sequência, identificador e dados
                sequencia, identificador, dados = UDP.desserialize(data)
                print(f"[DEBUG - receive_task] Sequência: {sequencia}, Identificador: {identificador}")

                # Verificar se a tarefa é direcionada ao agente correto
                if identificador == self.id:
                    task_data = dados.decode('utf-8')
                    print(f"[DEBUG - receive_task] Tarefa recebida e processada: {task_data}")

                    # Enviar um ACK de confirmação ao servidor
                    ack_message = UDP(tipo=99, dados=b'ACK', identificador=identificador, sequencia=sequencia)
                    self.sock.sendto(ack_message.serialize(), addr)
                    print(f"[DEBUG - receive_task] ACK enviado para o NMS_Server no endereço {addr}")

                    # Processar a tarefa recebida
                    self.process_task(task_data)
                else:
                    print(f"[DEBUG - receive_task] Tarefa não direcionada para este agente. Ignorada.")

            except Exception as e:
                print(f"[ERRO - receive_task] Falha ao receber mensagem: {e}")



    def process_task(self, task_data):
        # Converter JSON para dicionário
        task = json.loads(task_data)

        # Exemplo de operações:
        for device in task['devices']:
            device_id = device['device_id']
            metrics = device.get('device_metrics')
            link_metrics = device.get('link_metrics')
            alert_conditions = device.get('alertflow_conditions')
            
            # Chamar funções para monitoramento de métricas ou alertas
            self.collect_metrics(device_id, metrics, link_metrics)
            self.check_alerts(device_id, alert_conditions)


    # Implementar outras funções para coleta de métricas, enviar alertas, etc., conforme necessário

nms_agent = NMS_Agent(server_endereco="10.0.5.10", server_porta=5000)
nms_agent.connect_to_server()
nms_agent.receive_task()
