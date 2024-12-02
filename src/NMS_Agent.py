import socket, json, os, subprocess, re, psutil
from NetTask import UDP
from AlertFlow import TCP

debug = True

def debug_print(message):
    if debug:
        print(message)

class NMS_Agent:
    def __init__(self, server_endereco, tcp_porta, udp_porta):
        self.id = self.get_device_address()    # Obter o endereço IP do prórprio nodo
        self.server_endereco = server_endereco
        self.tcp_porta = tcp_porta
        self.udp_porta = udp_porta
        self.tcp_socket = None
        self.udp_socket = None
        self.metrics = {}

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

    # Usando a função registo do NetTask para registar o NMS_Agent
    def connect_to_UDP_server(self):
        mensagem_registo = UDP(
            tipo=1, 
            dados="", 
            identificador=self.id, 
            sequencia=1, 
            endereco=self.server_endereco, 
            porta=self.udp_porta, 
            socket=self.udp_socket
        )
        mensagem_registo.send_message()

    # Usando a função registo do AlertFlow para registar o NMS_Agent
    def connect_to_TCP_server(self):
        mensagem_registo = TCP(
            tipo=1, 
            dados="", 
            identificador=self.id, 
            endereco=self.server_endereco, 
            porta=self.tcp_porta,
            socket=self.tcp_socket
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
        # Exemplo de operações:
        device_id = task.get('device_id')
        metrics = task.get('device_metrics')
        link_metrics = task.get('link_metrics')
        alert_conditions = task.get('link_metrics').get('alertflow_conditions')
        self.perform_network_tests(device_id, link_metrics)

        # Chamar funções para monitoramento de métricas ou alertas

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

    def update_metric(self,metrics):
        for metric in metrics:
            if self.metrics[metric]:
                self.metrics[metric[0]] = tuple(self.metrics[metrics][0]+1,(self.metrics[metric][1]*self.metrics[metric][0] + metrics[metric][0])/self.metrics[metric][0]+1)
            else:
                self.metrics[metric[0]] = (1,metrics[metric])

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

    def get_metrics(self, command, stdout):
        # caso de ping
        metrics = []
        if command == 'ping':
            # Parse ping output
            packet_loss = re.search(r'(\d+)% packet loss', stdout).group(1)
            tuple = ('packet_loss',packet_loss)
            metrics.append(tuple)
            avg_time = re.search(r'avg = ([\d.]+)', stdout).group(1)
            metrics.append(tuple)
            debug_print(f"Packet Loss: {packet_loss}%, Average Time: {avg_time} ms")
            tuple = ('packet_loss',packet_loss)
            metrics.append(tuple)
            
        # caso de iperf
        elif command == 'iperf':
            # Parse iperf output
            bandwidth = re.search(r'(\d+ Mbits/sec)', stdout).group(1)
            tuple = ('bandwidth',bandwidth)
            metrics.append(tuple)
            debug_print(f"Bandwidth: {bandwidth}")
        else:
            debug_print("Comando desconhecido")
        cpu_usage = psutil.cpu_percent()
        tuple = ('cpu_usage',cpu_usage)
        metrics.append(tuple)
    
        ram_usage = psutil.virtual_memory().percent
        tuple = ('ram_usage',ram_usage)
        metrics.append(tuple)
        return metrics

    def run(self):
        global debug
        while True:
            print(f"Bem vindo Agente {self.id}")
            print("1 - Iniciar AlertFlow")
            print("2 - Iniciar NetTask")
            print("3 - Iniciar Tarefas")
            print("4 - Debug mode")
            print("0 - Sair")
            option = input("Digite a opção desejada: ")
            if option == "0":
                break
            elif option == "1":
                self.connect_to_TCP_server()
            elif option == "2":
                self.connect_to_UDP_server()
            elif option == "3":
                self.receive_task()
            elif option == "4":
                debug = not debug
                print(f"Debug mode {'ativado' if debug else 'desativado'}.")
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    nms_agent = NMS_Agent(server_endereco="10.0.5.10", tcp_porta=9000, udp_porta=5000)
    nms_agent.run()