import socket, os, glob, json, struct, threading, re,sys, queue, select
from AlertFlow import TCP
from NetTask import UDP
from Tarefa import Tarefa
from GUI import MetricsViewer

# Go to right folder 
# cd ../../../ && cd home/Documents/cc-2425

debug = False

def debug_print(message):
    if debug:
        print(message)

class NMS_Server:
    def __init__(self, config_path):
        self.config_path = config_path
        self.agents = {}  # Dicionário onde cada chave é o device_id e o valor é o endereço IP/porta do agente
        self.tasks = {}  # Dicionário onde cada chave é o device_id e o valor é a lista de tarefas a serem executadas
        self.tasks_loaded = {}  # Dicionário onde cada chave é o task_id e o valor é um booleano indicando se a tarefa foi concluída
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(None)
        self.udp_started = False
        self.tcp_started = False
        self.tcp_threads = []
        self.load_tasks_from_json()
        self.task_queue = queue.Queue()
        self.queue_event = threading.Event()

    # Lê todos os arquivos JSON na pasta de configurações
    def load_tasks_from_json(self,path = None):
        if not path:
            path = self.config_path
        json_files = glob.glob(os.path.join(path, '*.json'))
        tarefa = Tarefa(config_path=json_files,tasks_loaded= self.tasks_loaded)  # A instância de Tarefa já chama o load_file
        tdict = tarefa.dict
        tasks_to_be_deleted=[]
        for device in tdict:
            if device in self.agents:
                print(f"O dispositivo {device} já está registrado no servidor, enviando tarefa.")
                self.add_task((device, tdict[device]))
                tasks_to_be_deleted.append(device)
        for device in tasks_to_be_deleted:
            del tdict[device]
        if not self.tasks:
            self.tasks = tdict
        else :
            self.tasks.update(tdict)
        for task in tarefa.tasks:
            self.tasks_loaded[task] = True

    # Distribui as tarefas para os NMS_Agents via UDP
    def distribute_tasks(self,address,tasks_for_device):
        try:
            del self.tasks[address]
        except KeyError:
            print(f"Task from queue")
        agent_port = self.agents.get(address)[1]
        agent_ip = self.agents.get(address)[0]
        serialized_task = json.dumps(tasks_for_device, separators=(',', ':')).encode('utf-8')
        task_message = UDP(serialized_task, identificador=address, tipo=1, endereco=agent_ip, porta=agent_port, socket = self.udp_socket)
        debug_print(f"[DEBUG - Servidor] Distribuindo tarefas para o dispositivo {address}")
        if task_message.send_message():
            print(f"Tarefa enviada com sucesso para o dispositivo {address}.")
        else:
            print(f"Erro ao enviar a tarefa para o dispositivo {address}")

    def start_udp_server(self, devices_task_sent=[]):
        """Listens for incoming UDP connections. Must be threaded."""
        self.udp_started = True
        try:
            with self.udp_socket as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                LOCAL_ADR = "10.0.5.10"
                server_socket.bind((LOCAL_ADR, 5000))
                print("Servidor UDP esperando por conexões...")

                while self.udp_started:
                    # Use select to wait for either a socket event or a queue event
                    ready_sockets, _, _ = select.select([server_socket], [], [], 1)

                    # Check if there are tasks in the queue
                    if not self.task_queue.empty():
                        task = self.task_queue.get()
                        device = task[0]
                        agent_address = self.agents.get(device)
                        if agent_address:
                            # Send an ACK to the agent
                            ack_message = UDP(dados="", identificador=agent_address[0], tipo=98, endereco=agent_address[0],
                                                porta=agent_address[1], socket=server_socket)
                            ack_message.send_ack()

                            # Wait for an ACK response with retries and exponential backoff
                            max_retries = 3
                            delay = 2
                            ack_received = False
                            for attempt in range(max_retries):
                                try:
                                    server_socket.settimeout(delay)
                                    msg, client_address = server_socket.recvfrom(4096)  # Increased buffer size to 4096 bytes
                                    if not msg:
                                        continue

                                    # Deserialize the received message
                                    tipo, identificador, dados = UDP.desserialize(msg)
                                    if tipo == 98:
                                        debug_print(f"ACK recebido de {client_address}")
                                        # Send the task to the agent
                                        self.distribute_tasks(device, task[1])
                                        self.task_queue.task_done()
                                        ack_received = True
                                        break
                                except socket.timeout:
                                    debug_print(f"Timeout ao aguardar ACK (tentativa {attempt + 1})")
                                    delay *= 2  # Exponential backoff

                            if not ack_received:
                                debug_print("Falha ao receber ACK após várias tentativas. Movendo para a próxima tarefa...")
                                # Put the task back into the queue to retry later
                                self.task_queue.put(task)
                        else:
                            # If the agent address is not found, mark the task as done
                            self.task_queue.task_done()

                        # If the queue is empty, clear the event
                        if self.task_queue.empty():
                            self.queue_event.clear()
                    elif ready_sockets: # recebe registo
                        try:
                            msg, client_address = server_socket.recvfrom(4096)  # Increased buffer size to 4096 bytes
                            if not msg:
                                print("Mensagem vazia recebida. Continuando...")
                                continue

                            print(f"Mensagem recebida de {client_address}")
                            # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                            tipo, identificador, dados = UDP.desserialize(msg)
                            debug_print(f"[DEBUG - dados udp] Dados desserializados - Tipo: {tipo}, Identificador: {identificador}, Dados: {dados}")
                            # Criando o ACK como uma instância UDP
                            if tipo == 99:
                                ack_message = UDP(dados="", identificador=identificador, tipo=98, endereco=client_address[0], 
                                                    porta=client_address[1], socket=server_socket)
                                ack_message.send_ack()

                                # Guardar ip do agente que acabou de se ligar
                                self.agents[identificador] = (client_address[0], client_address[1])
                                print(f"Agentes registrados no servidor: {self.agents}")
                                debug_print(f"[DEBUG - agentes] Agentes registrados no servidor: {self.agents}")
                                print(client_address[0])
                                try :
                                    client_tasks = self.tasks[client_address[0]]
                                    self.distribute_tasks(client_address[0],client_tasks)
                                except KeyError:
                                    print("Nenhuma tarefa para enviar para este agente")
                                    ack_message = UDP(dados="", identificador=identificador, tipo=99, endereco=client_address[0], 
                                                    porta=client_address[1], socket=server_socket)
                                    ack_message.send_ack()
                            elif tipo == 96:
                                debug_print("[DEBUG] Recebido ack de iperf porta")
                                ack_message = UDP(dados="", identificador=identificador, tipo=96, endereco=client_address[0], 
                                                    porta=client_address[1], socket=server_socket)
                                ack_message.send_ack()
                                try:
                                    msg, client_address = server_socket.recvfrom(4096)  # Increased buffer size to 4096 bytes
                                    if not msg:
                                        print("Mensagem vazia recebida. Continuando...")
                                        continue

                                    print(f"Mensagem recebida de {client_address}")
                                    # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                                    tipo, identificador, dados = UDP.desserialize(msg)
                                    debug_print(f"[DEBUG - dados udp] Dados desserializados - Tipo: {tipo}, Identificador: {identificador}, Dados: {dados}")
                                    iperf_server = self.agents.get(dados)
                                    print(f"Agentes registrados no servidor: {self.agents}")
                                    ack_iperf = UDP(dados="", identificador=identificador, tipo=96, endereco=client_address[0], 
                                               porta=client_address[1], socket=self.udp_socket)
                                    ack_iperf.send_ack()
                                    print(f"IPERF SERVER: {iperf_server}")
                                    server = str(iperf_server[1])
                                    ack_message = UDP(dados=server, identificador=identificador, tipo=2, endereco=client_address[0], 
                                                      porta=client_address[1], socket=server_socket)
                                    ack_message.send_message()
                                    print(f"Enviando iperf server {iperf_server} para {client_address[0]}")
                                except socket.timeout:
                                    print("Tempo limite do socket atingido. Continuando...")
                                    pass
                            else :
                                print("Ack recebido nao e de registo")
                        except socket.timeout:
                            print("Tempo limite do socket atingido. Continuando...")
                            pass
        except struct.error as e:
            print("Erro ao desserializar a mensagem:", e)
        except OSError as e:
            print(f"OSError: {e}")

    def add_task(self, task):
        self.task_queue.put(task)
        self.queue_event.set()

    def start_tcp_server(self):
        """Listens for incoming TCP connections. Must be threaded. Passive method should close the connection, not the socket."""
        self.tcp_started = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                LOCAL_ADR = "10.0.5.10"
                server_socket.bind((LOCAL_ADR, 9000))
                server_socket.listen(5)
                debug_print("Servidor TCP esperando por conexões de alertas...")
    
                while self.tcp_started:
                    conn, addr = server_socket.accept()
                    debug_print(f"Conectado por {addr}")
                    thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
                    self.tcp_threads.append(thread)
                    thread.start()
        except Exception as e:
            debug_print(f"Error while setting up server on {LOCAL_ADR}:9000: {e}")
        finally:
            for thread in self.tcp_threads:
                thread.join()
    
    def handle_connection(self, conn, addr):
        with conn:
            msg = conn.recv(1024)
            if msg:
                alert_type, device_id, current_value = TCP.deserialize_tcp(msg)
                debug_print(f"Alerta recebido do dispositivo {device_id}: {alert_type}, Valor atual: {current_value}")

    def start_gui(self):
        metrics_viewer = MetricsViewer()
        metrics_viewer.start()
    
    def run(self):
        global debug
        while True:
            print("Iniciando servidor NMS...")
            print("1 - Iniciar socket TCP")
            print("2 - Iniciar socket UDP")
            print("3 - Load new tasks")
            print("4 - Debug mode")
            print("5 - GUI")
            print("0 - Sair")
            option = input("Digite a opção desejada: ")
            if option == "0":
                break
            elif option == "1":
                if not self.tcp_started:
                    threading.Thread(target=self.start_tcp_server,daemon=True).start()
                else:
                    print("Servidor TCP já está em execução.")
            elif option == "2":
                if not self.udp_started:
                    threading.Thread(target=self.start_udp_server,daemon=True).start()
                else:
                    print("Servidor UDP já está em execução.")
            elif option == "3":
                path = input("Digite o caminho da pasta de tarefas: ")
                self.load_tasks_from_json(path)
            elif option == "4":
                debug = not debug
                print(f"Debug mode {'ativado' if debug else 'desativado'}.")
            elif option == "5":
                # Iniciar a GUI em uma thread separada
                threading.Thread(target=self.start_gui, daemon=True).start()

            else:
                print("Opção inválida. Tente novamente.")
        sys.exit()


# Executando o servidor NMS
if __name__ == "__main__":
    config_path = "./dataset"
    server = NMS_Server(config_path)
    server.run()