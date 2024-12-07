import socket, json, os, subprocess, re, psutil, time, threading, sys
from NetTask import UDP, send_ack_get_reply
from AlertFlow import TCP

debug = True
performing_task = False

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
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tasks = []
        self.metrics = {}
        self.last_ack_time = 0  # Timestamp of the last received ACK

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
        #self.udp_socket.settimeout(5)  # Set a timeout for the UDP socket

        # Step 1: Send an ACK to the server
        ack_message = UDP(
            dados="", 
            identificador=self.id, 
            tipo=99, 
            endereco=self.server_endereco, 
            porta=self.udp_porta, 
            socket=self.udp_socket
        )
        ack_message.send_ack()
        print(f"[DEBUG - connect_to_UDP_server] Enviado ACK de registo para {self.server_endereco}:{self.udp_porta}")
        # Step 2: Receive an ACK from the server
        try:
            while True:
                msg, server_address = self.udp_socket.recvfrom(4096)
                if not msg:
                    continue

                # Deserialize the received message
                tipo, identificador, dados = UDP.desserialize(msg)
                if identificador == self.id and tipo == 99:
                    debug_print(f"ACK recebido do servidor {server_address}")
                    break
                if identificador == self.id and tipo == 98:
                    debug_print(f"ACK recebido indicando que nao ha tarefas atualmente para este agente")
                    self.receive_task()
                    return
        except socket.timeout:
            print("Tempo limite atingido ao esperar pelo ACK do servidor. Tentando novamente...")
            self.connect_to_UDP_server()  # Retry connecting to the server

        # Step 3: Receive the task from the server
        try:
            while True:
                msg, server_address = self.udp_socket.recvfrom(4096)
                if not msg:
                    continue

                # Deserialize the received message
                tipo, identificador, dados = UDP.desserialize(msg)
                if identificador == self.id and tipo == 1:
                    debug_print(f"Tarefa recebida do servidor {server_address}")
                    
                    self.tasks = json.loads(dados)  # Store the received tasks
                    ack_message = UDP(
                    dados="", 
                    identificador=self.id, 
                    tipo=98, 
                    endereco=self.server_endereco, 
                    porta=self.udp_porta, 
                    socket=self.udp_socket
                    )
                    ack_message.send_ack()
                    print(f"[DEBUG - connect_to_UDP_server] Enviado ACK de tarefas inicias para {self.server_endereco}:{self.udp_porta}")
                    self.process_task()  # Process the received tasks
                    break
        except socket.timeout:
            print("Tempo limite atingido ao esperar pela tarefa do servidor. Tentando novamente...")
            self.connect_to_UDP_server()  # Retry connecting to the server

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
        self.tcp_socket = mensagem_registo.socket
        mensagem_registo.send_message()

    # No método receive_task do agente
    def receive_task(self):
        debug_print("[DEBUG - receive_task] Aguardando tarefas do NMS_Server...")
        while True:
            try:
                # Recebe a mensagem e o endereço de onde ela foi enviada
                data, addr = self.udp_socket.recvfrom(4096)
                debug_print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                # Desserializar a mensagem recebida para extrair o tipo, identificador e dados
                tipo, identificador, dados = UDP.desserialize(data)
                debug_print(f"[DEBUG - receive_task] Tipo: {tipo}, Identificador: {identificador}")

                # Verificar se a tarefa é direcionada ao agente correto
                if identificador == self.id:
                    if not tipo == 99 and not tipo == 98:
                        self.tasks = json.loads(dados)
                        # Enviar um ACK de confirmação ao servidor
                        ack_message = UDP(dados='', identificador=identificador, tipo=98, endereco=self.server_endereco, 
                                            porta=self.udp_porta, socket=self.udp_socket)
                        debug_print(f"[DEBUG - receive_task] Enviando ACK apos receber mais tarefas para {self.server_endereco}:{self.udp_porta}")
                        ack_message.send_ack()
                        # Processar a tarefa recebida
                        debug_print(f"[DEBUG - receive_task] Processando tarefas")
                        self.process_task()
                    elif tipo == 99:
                        debug_print("[DEBUG - receive_task] Faulty ack.")
                        debug_print("[DEBUG - receive_task] Aguardando tarefas do NMS_Server...")
                    else : 
                        ack_message = UDP(dados="", identificador=identificador, tipo=98, endereco=self.server_endereco, 
                                               porta=self.udp_porta, socket=self.udp_socket)
                        ack_message.send_ack()
                        debug_print(f"[DEBUG - receive_task] Enviando ACK apos receber ACK para {self.server_endereco}:{self.udp_porta}")
                else:
                    debug_print(f"[DEBUG - receive_task] Tarefa não direcionada para este agente. Ignorada.")

            except socket.timeout:
                debug_print("[DEBUG - receive_task] Tempo esgotado. Nenhuma mensagem recebida.")
                continue  # Volta para aguardar a próxima mensagem

            except Exception as e:
                print(f"[ERRO - receive_task] Falha ao receber mensagem: {e}")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

    def iperf_connection(self, role,comand,server_address=None):
        if role == 'client':
            #ack_iperf = UDP(dados="", identificador=self.id, tipo=96, endereco=self.server_endereco, 
            #                                   porta=self.udp_porta, socket=self.udp_socket)
            #ack_iperf.send_ack()
            #try:
            #    # Recebe a mensagem e o endereço de onde ela foi enviada
            #   data, addr = self.udp_socket.recvfrom(4096)
            #    debug_print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta#

            #    # Desserializar a mensagem recebida para extrair o tipo, identificador e dados
            #    tipo, identificador, dados = UDP.desserialize(data)
            #    debug_print(f"[DEBUG - receive_task] Tipo: {tipo}, Identificador: {identificador}")
            #    if tipo == 96:
            send_ack_get_reply(self.id,96, self.server_endereco, self.udp_porta,self.udp_socket)
            iperf_message = UDP(dados=server_address, identificador=self.id, tipo=2, endereco=self.server_endereco,
                                porta= self.udp_porta, socket=self.udp_socket)
            iperf_message.send_message()

            debug_print(f"[DEBUG - receive_task] Ack apos mandar")
            ack_iperf = UDP(dados="", identificador=self.id, tipo=96, endereco=self.server_endereco, 
                                        porta=self.udp_porta, socket=self.udp_socket)
            ack_iperf.send_ack()
            try:
                # Recebe a mensagem e o endereço de onde ela foi enviada
                data, addr = self.udp_socket.recvfrom(4096)
                debug_print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                # Desserializar a mensagem recebida para extrair o tipo, identificador e dados
                tipo, identificador, dados = UDP.desserialize(data)
                debug_print(f"[DEBUG - receive_task] Tipo: {tipo}, Identificador: {identificador}")
                print(dados)
                iperf_porta = dados
                ack_iperf = UDP(dados="", identificador=self.id, tipo=96, endereco=self.server_endereco, 
                                        porta=self.udp_porta, socket=self.udp_socket)
                ack_iperf.send_ack()
                print(f"[DEBUG - receive_task] Iperf porta: {iperf_porta}")
                # comunicar com agent que vai ser servidor do iperf
                porta = int(iperf_porta)
                ack_iperf = UDP(dados="", identificador=self.id, tipo=96, endereco=server_address, 
                                        porta=porta, socket=self.udp_socket)
                ack_iperf.send_ack()
                try:
                    # Recebe a mensagem e o endereço de onde ela foi enviada
                    data, addr = self.udp_socket.recvfrom(4096)
                    debug_print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                    # Desserializar a mensagem recebida para extrair o tipo, identificador e dados
                    tipo, identificador, dados = UDP.desserialize(data)
                    debug_print(f"[DEBUG - receive_task] Tipo: {tipo}, Identificador: {identificador}")

                    try:    
                        response = subprocess.run(comand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=40)
                        #if "Connection refused" in response.stderr:
                        #    debug_print(f"[DEBUG - perform_network_tests] Connection refused: {response.stderr}")
                        debug_print(f"[DEBUG - perform_network_tests] Iperf response: {response.stdout}")
                        return response.stdout
                    except subprocess.TimeoutExpired:
                        debug_print(f"[DEBUG - perform_network_tests] Iperf test timed out.")
                        return None
                    except Exception as e:
                        debug_print(f"[DEBUG - perform_network_tests] Error: {e}")
                        return None

                except socket.timeout:
                    debug_print("[DEBUG - receive_task] Tempo esgotado. Nenhuma mensagem recebida.")
                    return
            except socket.timeout: 
                debug_print("[DEBUG - receive_task] Tempo esgotado. Nenhuma mensagem recebida.")
                return
        else:
            try:
                print("Aguardando conexão de um cliente iperf...")
                # Recebe a mensagem e o endereço de onde ela foi enviada
                data, addr = self.udp_socket.recvfrom(4096)
                debug_print(f"[DEBUG - receive_task] Mensagem recebida de {addr[0]} na porta {addr[1]}")  # addr[0] -> IP, addr[1] -> Porta

                # Desserializar a mensagem recebida para extrair o tipo, identificador e dados
                tipo, identificador, dados = UDP.desserialize(data)
                debug_print(f"[DEBUG - receive_task] Tipo: {tipo}, Identificador: {identificador}")
                ack_iperf = UDP(dados="", identificador=self.id, tipo=96, endereco=addr[0], 
                                               porta=addr[1], socket=self.udp_socket)
                ack_iperf.send_ack()
                try:    
                    response = subprocess.run(comand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=40)
                    #if "Connection refused" in response.stderr:
                    #    debug_print(f"[DEBUG - perform_network_tests] Connection refused: {response.stderr}")
                    debug_print(f"[DEBUG - perform_network_tests] Iperf response: {response.stdout}")
                    return response.stdout
                except subprocess.TimeoutExpired:
                    debug_print(f"[DEBUG - perform_network_tests] Iperf test timed out.")
                    return None
                except Exception as e:
                    debug_print(f"[DEBUG - perform_network_tests] Error: {e}")
                    return None
            except socket.timeout:
                debug_print("[DEBUG - receive_task] Tempo esgotado. Nenhuma mensagem recebida.")
                return

    def ping_connection(self,comand):
        try:
            response = subprocess.run(comand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=40)
            if "Connection refused" in response.stderr:
                debug_print(f"[DEBUG - perform_network_tests] Connection refused: {response.stderr}")
                return None
            debug_print(f"[DEBUG - perform_network_tests] Ping response: {response.stdout}")
            return response.stdout
        except subprocess.TimeoutExpired:
            debug_print(f"[DEBUG - perform_network_tests] Ping test timed out.")
        except Exception as e:
            debug_print(f"[DEBUG - perform_network_tests] Error: {e}")

    def process_task(self):
        for task in self.tasks:
            debug_print(f"[DEBUG - process_task] Processando tarefa {task[0]}")
            frequency = task[1].get('frequency')
            device_metrics = task[1].get('device_metrics')
            link_metrics = task[1].get('link_metrics')
            alert_conditions = task[1].get('alertflow_conditions')
            self.task_manager(device_metrics, link_metrics, alert_conditions, frequency)
            debug_print(f"[DEBUG - process_task] Tarefa {task[0]} processada com sucesso.")

        self.tasks = []
        print("Todas as tarefas foram processadas com sucesso.")
        print("Tentando adquirir novas tarefas...")
        self.receive_task()

    def task_manager(self, device_metrics, link_metrics, alert_conditions, frequency):
        cpu_usage = False
        ram_usage = False
        if device_metrics.get('cpu_usage') == True:
            cpu_usage = device_metrics.get('cpu_usage')
        if device_metrics.get('ram_usage') == True:
            ram_usage = device_metrics.get('ram_usage')
        print(json.dumps(link_metrics, indent=4))
        for command in link_metrics:
            debug_print(f"[DEBUG - task_manager] Executando comando {command}")
            performing_task = True
            if command == 'iperf':
                bandwidth = link_metrics.get(command).get('bandwidth')
                packet_loss = link_metrics.get(command).get('packet_loss')
                jitter = link_metrics.get(command).get('jitter')
                if jitter == 'true':
                    jitter_threshold = alert_conditions.get('jitter_threshold')
                if bandwidth == 'true':
                    bandwidth_threshold = alert_conditions.get('bandwidth_threshold')
                if bandwidth or jitter or packet_loss:
                    tool_settings = {
                        'role' : link_metrics.get(command).get('role'),
                        'server_address' : link_metrics.get(command).get('server_address') if link_metrics.get(command).get('role') == 'client' else None,
                        'duration' : link_metrics.get(command).get('duration'),
                        'frequency' : link_metrics.get(command).get('frequency'),
                        'transport' : link_metrics.get(command).get('transport')
                    }
                else :
                    print("Nenhuma métrica a ser medida.")
            elif command == 'ping':
                latency = link_metrics.get(command).get('latency')
                if latency:
                    debug_print("[DEBUG - task_manager] Executando teste de latência...")
                    command = 'ping'
                    tool_settings = {
                        'destination' : link_metrics.get(command).get('destination'),
                        'frequency' : link_metrics.get(command).get('frequency'),
                        'duration' : link_metrics.get(command).get('duration'),
                    }
                    #metrics = self.get_metrics('ping',output)
            if ram_usage == 'true':
                ram_usage_threshold = alert_conditions.get('ram_usage_threshold')
            if cpu_usage == 'true':
                cpu_usage_threshold = alert_conditions.get('cpu_usage_threshold')
            
            
            #threading.Thread(target=self.monitor_task, args=(frequency,alert_conditions, ram_usage, cpu_usage)).start() 
            command = self.parse_command(command,tool_settings)
            output = None
            if command[0] == 'ping':
                output = self.ping_connection(command)
            elif command[0] == 'iperf':
                output = self.iperf_connection(tool_settings.get('role'),command,tool_settings.get('server_address'))
            metrics = self.get_metrics(command,output)
            self.update_metric(metrics)
            debug_print(f"[DEBUG - task_manager] Métricas atualizadas: {metrics}")
            print(json.dumps(self.metrics, indent=4))
            #metrics = self.get_metrics('iperf',output)
            performing_task = False
    
        #metrics_message = UDP(tipo=3, dados=self.metrics, identificador=self.id, endereco=self.server_endereco, porta=self.udp_porta, socket=self.udp_socket)
        #metrics_message.send_message()
        self.metrics = {}
        # Verifica se os thresholds foram ultrapassados

    def monitor_task(self,frequency,alert_conditions, ram_usage, cpu_usage):
        while performing_task:
            time.sleep(frequency)
            for condition in alert_conditions:
                if ram_usage and psutil.virtual_memory() > condition.get('ram_usage_threshold'):
                    message = f"Alerta: RAM usage ultrapassou o threshold."
                    print(message)
                    alert = TCP(tipo=2, dados=message, identificador=self.id, endereco=self.server_endereco, porta=self.tcp_porta, socket=self.tcp_socket)
                    if alert.send_message():
                        print("Alerta enviado com sucesso.")
                    else:
                        print("Erro ao enviar alerta.")
                if cpu_usage and psutil.cpu_usage() > condition.get('cpu_usage_threshold'):
                    print(f"Alerta: CPU usage ultrapassou o threshold.")
                if self.metrics.get('bandwidth') > condition.get('bandwidth_threshold'):
                    print(f"Alerta: Bandwidth no dispositivo ultrapassou o threshold.")
                if self.metrics.get('latency') > condition.get('latency_threshold'):
                    print(f"Alerta: Latency ultrapassou o threshold.")
                if self.metrics.get('jitter') > condition.get('jitter_threshold'):
                    print(f"Alerta: Jitter ultrapassou o threshold.")
                if self.metrics.get('packet_loss') > condition.get('packet_loss_threshold'):
                    print(f"Alerta: Packet loss ultrapassou o threshold.")

    def update_metric(self,metrics):
        for metric in metrics:
            dict_metric = self.metrics.get(metric[0])
            if dict_metric:
                count = dict_metric[0] + 1
                avg = (dict_metric[1]*dict_metric[0] + metric[1])/count
                self.metrics[metric[0]] = (count, avg)
            else:
                self.metrics[metric[0]]=(1,metric[1])

    # Função para realizar aplicar as tarefas
    def parse_command(self, tool, tool_settings):
        # Example of using ping
        debug_print(f"[DEBUG - perform_network_tests] Tool: {tool}")
        comand = []
        if 'ping' in tool:
            comand = ["ping"]
            duration = tool_settings.get('duration')
            comand.append("-c")
            comand.append(str(duration))
            comand.append(tool_settings.get('destination'))
            
        # Example of using iperf
        if 'iperf' in tool:

            response = None
            duration = tool_settings.get('duration')
            role = tool_settings.get('role')
            transport = tool_settings.get('transport')
            comand = ["iperf"]
            if role == "client":
                comand.append("-c")
                server = tool_settings.get('server_address')
                comand.append(server)
                if transport == "udp":
                    comand.append("-u")
                comand.append("-b")
                comand.append(f"{duration*100}M")
            else:
                comand.append("-s")
                if transport == "udp":
                    comand.append("-u")
                comand.append("-P")
                comand.append("-1")
        return comand

    def get_metrics(self, command, stdout):
        metrics = []

        if stdout is None:
            return metrics

        if command[0] == 'ping':
            # Parse ping output
            packet_loss_match = re.search(r'(\d+)% packet loss', stdout)
            if packet_loss_match:
                packet_loss = packet_loss_match.group(1)
                metrics.append(('packet_loss', packet_loss))
            
            avg_time_match = re.search(r'avg = ([\d.]+)', stdout)
            if avg_time_match:
                avg_time = avg_time_match.group(1)
                metrics.append(('avg_time', avg_time))
            
                debug_print(f"Packet Loss: {packet_loss}%, Average Time: {avg_time} ms")
        
        elif command[0] == 'iperf':
            # Parse iperf output
            bandwidth_match = re.search(r'(\d+) Mbits/sec', stdout)
            if bandwidth_match:
                bandwidth = bandwidth_match.group(1)
                metrics.append(('bandwidth', bandwidth))
            
                debug_print(f"Bandwidth: {bandwidth} Mbits/sec")
        
        else:
            debug_print("Comando desconhecido")
        
        cpu_usage = psutil.cpu_percent()
        metrics.append(('cpu_usage', cpu_usage))
        
        ram_usage = psutil.virtual_memory().percent
        metrics.append(('ram_usage', ram_usage))
        
        print(f"[DEBUG - get_metrics] Metrics : {metrics}")
        return metrics

    def run(self):
        global debug
        while True:
            print(f"Bem vindo Agente {self.id}")
            print("1 - Iniciar AlertFlow")
            print("2 - Iniciar NetTask")
            print("3 - Debug mode")
            print("0 - Sair")
            option = input("Digite a opção desejada: ")
            if option == "0":
                break
            elif option == "1":
                self.connect_to_TCP_server()
            elif option == "2":
                self.connect_to_UDP_server()
            elif option == "3":
                debug = not debug
                print(f"Debug mode {'ativado' if debug else 'desativado'}.")
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    nms_agent = NMS_Agent(server_endereco="10.0.5.10", tcp_porta=9000, udp_porta=5000)
    nms_agent.run()