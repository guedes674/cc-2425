import socket, json
from NetTask import UDP

class NMS_Agent:
    def __init__(self, server_endereco, server_porta):
        self.id = self.get_device_address()    # Obter o endereço IP do prórprio nodo
        self.server_endereco = server_endereco
        self.server_porta = server_porta

        # Criar o socket UDP para comunicação com o servidor
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


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
        mensagem_registo = UDP(
            tipo=1, 
            dados="", 
            identificador=self.id, 
            sequencia=1, 
            endereco=self.server_endereco, 
            porta=self.server_porta, 
            sock=self.sock
        )
        mensagem_registo.send_message()

    # No método receive_task do agente
    def receive_task(self):
        print("[DEBUG - receive_task] Aguardando tarefas do NMS_Server...")
        while True:
            try:
                # Recebe a mensagem e o endereço de onde ela foi enviada
                data, addr = self.sock.recvfrom(4096)
                print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                # Desserializar a mensagem recebida para extrair a sequência, identificador e dados
                sequencia, identificador, dados = UDP.desserialize(data)
                print(f"[DEBUG - receive_task] Sequência: {sequencia}, Identificador: {identificador}")

                # Verificar se a tarefa é direcionada ao agente correto
                if identificador == self.id:
                    task_data = dados
                    print(f"[DEBUG - receive_task] Tarefa recebida e processada: {task_data}")

                    # Enviar um ACK de confirmação ao servidor
                    ack_message = UDP(tipo=99, dados='', identificador=identificador, sequencia=sequencia, endereco=self.server_endereco, 
                                      porta=self.server_porta, sock=self.sock)
                    print(f"[DEBUG - send_ack] Enviando ACK para {self.server_endereco}:{self.server_porta}")
                    ack_message.send_ack()

                    # Processar a tarefa recebida
                    self.process_task(task_data)
                else:
                    print(f"[DEBUG - receive_task] Tarefa não direcionada para este agente. Ignorada.")

            except socket.timeout:
                print("[DEBUG - receive_task] Tempo esgotado. Nenhuma mensagem recebida.")
                continue  # Volta para aguardar a próxima mensagem

            except Exception as e:
                print(f"[ERRO - receive_task] Falha ao receber mensagem: {e}")



    def process_task(self, task_data):
        # Converter JSON para dicionário
        task = json.loads(task_data)

        # Exemplo de operações:
        for device in task['devices']:
            device_id = device.get('device_id')
            metrics = device.get('device_metrics')
            link_metrics = device.get('link_metrics')
            alert_conditions = device.get('alertflow_conditions')

        # Chamar funções para monitoramento de métricas ou alertas
        self.collect_metrics(device_id, metrics, link_metrics)
        self.check_alerts(device_id, alert_conditions)

    def collect_metrics(self, device_id, metrics, link_metrics):
        print(f"[DEBUG - collect_metrics] Coletando métricas para o dispositivo {device_id}")

        if metrics:
            print(f"[DEBUG - collect_metrics] Métricas do dispositivo: {metrics}")
            # Processar métricas do dispositivo
            for metric, value in metrics.items():
                print(f"[DEBUG - collect_metrics] Métrica: {metric}, Valor: {value}")
                # Adicione lógica para processar cada métrica

        if link_metrics:
            print(f"[DEBUG - collect_metrics] Métricas de link: {link_metrics}")
            # Processar métricas de link
            for link, link_value in link_metrics.items():
                print(f"[DEBUG - collect_metrics] Link: {link}, Valor: {link_value}")
                # Adicione lógica para processar cada métrica de link

        # Adicione lógica para armazenar ou enviar as métricas coletadas
        print(f"[DEBUG - collect_metrics] Coleta de métricas concluída para o dispositivo {device_id}")

    def check_alerts(self, device_id, alert_conditions):
        print(f"[DEBUG - check_alerts] Verificando alertas para o dispositivo {device_id}")

        if alert_conditions:
            print(f"[DEBUG - check_alerts] Condições de alerta: {alert_conditions}")
            # Processar condições de alerta
            for alert, condition in alert_conditions.items():
                print(f"[DEBUG - check_alerts] Alerta: {alert}, Condição: {condition}")
                # Adicione lógica para verificar cada condição de alerta

        # Adicione lógica para enviar alertas ou notificações
        print(f"[DEBUG - check_alerts] Verificação de alertas concluída para o dispositivo {device_id}")

    # Implementar outras funções para coleta de métricas, enviar alertas, etc., conforme necessário


if __name__ == "__main__":
    nms_agent = NMS_Agent(server_endereco="10.0.5.10", server_porta=5000)
    nms_agent.connect_to_server()
    nms_agent.receive_task()