import socket, json
from NetTask import UDP
import os
import subprocess
class NMS_Agent:
    def __init__(self, server_endereco, server_porta):
        self.id = self.get_device_address()    # Obter o endereço IP do prórprio nodo
        self.server_endereco = server_endereco
        self.server_porta = server_porta
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Obtém o endereço IP local do dispositivo (ID do NMS_Agent)
    def get_device_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
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
            socket=self.socket
        )
        mensagem_registo.send_message()

    # No método receive_task do agente
    def receive_task(self):
        print("[DEBUG - receive_task] Aguardando tarefas do NMS_Server...")
        while True:
            try:
                # Recebe a mensagem e o endereço de onde ela foi enviada
                data, addr = self.socket.recvfrom(4096)
                print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                # Desserializar a mensagem recebida para extrair a sequência, identificador e dados
                sequencia, identificador, dados = UDP.desserialize(data)
                print(f"[DEBUG - receive_task] Sequência: {sequencia}, Identificador: {identificador}")

                # Verificar se a tarefa é direcionada ao agente correto
                if identificador == self.id:
                    task_data = json.loads(dados)
                    print(f"[DEBUG - receive_task] Tarefa recebida e processada: {task_data.get('task_id')}")

                    # Enviar um ACK de confirmação ao servidor
                    ack_message = UDP(tipo=99, dados='', identificador=identificador, sequencia=sequencia, endereco=self.server_endereco, 
                                      porta=self.server_porta, socket=self.socket)
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

    def process_task(self, task):
        # Converter JSON para dicionário

        # Exemplo de operações:
        device_id = task.get('device_id')
        metrics = task.get('device_metrics')
        link_metrics = task.get('link_metrics')
        alert_conditions = task.get('link_metrics').get('alertflow_conditions')
        self.perform_network_tests(device_id, link_metrics)

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

    # Função para realizar aplicar as tarefas
    def perform_network_tests(self, device_id, link_metrics):
        # Example of using ping
        for metric in link_metrics:
            tool = link_metrics.get(metric).get('tool')
            print(f"[DEBUG - perform_network_tests] Metric: {metric}")
            print(f"[DEBUG - perform_network_tests] Tool: {tool}")
            if 'ping' in tool:
                if device_id:
                    duration = link_metrics.get(metric).get('duration')
                    frequency = link_metrics.get(metric).get('frequency')   
                    destination = link_metrics.get(metric).get('destination')
                    response = os.system(f"ping -c {frequency} {destination}")
                    print(f"[DEBUG - perform_network_tests] Ping response for {device_id}: {response}")

            # Example of using iperf
            if 'iperf' in tool:
                duration = link_metrics.get(metric).get('duration')
                mode = link_metrics.get(metric).get('mode')
                transport = link_metrics.get(metric).get('transport')
                server = link_metrics.get(metric).get('server_address')
                comand = ["iperf"]
                if mode == "client":
                    comand.append("-c")
                    comand.append(server)
                    if transport == "udp":
                        comand.append("-u")
                    comand.append("-b")
                    comand.append(f"{duration*100}M")
                else:
                    comand.append("-s")
                    if transport == "udp":
                        comand.append("-u")
                    comand.append("-1")

                #response = os.system(f"iperf {'-c' if mode == 'client' else '-s'} {server if mode =='client' else ''} {'-u' if transport == 'udp' else ''} -b {duration*100}M")
                try :
                    response = subprocess.run(comand, stdout=subprocess.PIPE,text=True)
                    response.wait(timeout = 20)
                except subprocess.TimeoutExpired:
                    print(f"[DEBUG - perform_network_tests] Iperf test timed out.")
                    response.terminate()
                print(f"[DEBUG - perform_network_tests] Iperf response for {device_id}: {response.stdout}")

if __name__ == "__main__":
    nms_agent = NMS_Agent(server_endereco="10.0.5.10", server_porta=5000)
    nms_agent.connect_to_server()
    nms_agent.receive_task()