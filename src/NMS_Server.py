import socket, os, glob, json, struct, threading, re,sys
from AlertFlow import TCP
from NetTask import UDP
from Tarefa import Tarefa

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

    # Lê todos os arquivos JSON na pasta de configurações
    def load_tasks_from_json(self,path = None):
        if not path:
            path = self.config_path
        json_files = glob.glob(os.path.join(path, '*.json'))
        tarefa = Tarefa(config_path=json_files,tasks_loaded= self.tasks_loaded)  # A instância de Tarefa já chama o load_file
        for device in tarefa.dict:
            if device in self.agents:
                print(f"O dispositivo {device} já está registrado no servidor, enviando tarefa.")
                self.tasks[device] = tarefa.dict.get(device)
                self.distribute_tasks(device)
        if not self.tasks:
            self.tasks = tarefa.dict
        else :
            self.tasks.update(tarefa.dict)
        for task in tarefa.tasks:
            self.tasks_loaded[task] = True

    # Distribui as tarefas para os NMS_Agents via UDP
    def distribute_tasks(self,address):
        if not self.tasks:
            print("Nenhuma tarefa carregada para distribuição.")
            return
        tasks_for_device = self.tasks.get(address)
        try:
            del self.tasks[address]
        except KeyError:
            print(f"Erro ao remover a tarefa para o dispositivo {address}")
        agent_port = self.agents.get(address)[1]
        agent_ip = self.agents.get(address)[0]
        serialized_task = json.dumps(tasks_for_device, separators=(',', ':')).encode('utf-8')
        task_message = UDP(2, serialized_task, identificador=address, sequencia=1, endereco=agent_ip, porta=agent_port, socket = self.udp_socket)
        debug_print(f"[DEBUG - Servidor] Distribuindo tarefas para o dispositivo {address}")
        if task_message.send_message():
            print(f"Tarefa enviada com sucesso para o dispositivo {address}.")
        else:
            print(f"Erro ao enviar a tarefa para o dispositivo {address}")


    def place_holder(self):
        if not self.tasks:
            print("Nenhuma tarefa carregada para monitoramento.")
            return

        for task in self.tasks:
            task_id = task.tasks[0]['task_id']
            frequency = task.tasks[0]['frequency']
            devices = task.tasks[0]['devices']

            for device in devices:
                thread = threading.Thread(target=self.monitoring_task, args=(task))
                thread.start()

    def start_udp_server(self, devices_task_sent=[]):
        """Listens for incoming UDP connections. Must be threaded."""
        self.udp_started = True
        try:
            with self.udp_socket as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                LOCAL_ADR = "10.0.5.10"
                server_socket.bind((LOCAL_ADR, 5000))
                server_socket.settimeout(None)  # Garantir que o socket não tenha um tempo limite
                print("Servidor UDP esperando por conexões...")

                while self.udp_started:
                    try:
                        msg, client_address = server_socket.recvfrom(1024)
                        if not msg:
                            print("Mensagem vazia recebida. Continuando...")
                            continue

                        print(f"Mensagem recebida de {client_address}")

                        # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                        sequencia, identificador, dados = UDP.desserialize(msg)
                        debug_print(f"[DEBUG - dados udp] Dados desserializados - Sequência: {sequencia}, Identificador: {identificador}, Dados: {dados}")
                        # Criando o ACK como uma instância UDP
                        ack_message = UDP(tipo=99, dados="", identificador=identificador, sequencia=sequencia, endereco=client_address[0], 
                                            porta=client_address[1], socket=server_socket)
                        ack_message.send_ack()

                        # Guardar ip do agente que acabou de se ligar
                        self.agents[identificador] = (client_address[0], client_address[1])
                        debug_print(f"[DEBUG - agentes] Agentes registrados no servidor: {self.agents}")
                        self.distribute_tasks(client_address[0])
                        #self.initialize_tasks(devices_task_sent)
                    except socket.timeout:
                        print("Tempo limite do socket atingido. Continuando...")
                        pass
                
        except struct.error as e:
            print("Erro ao desserializar a mensagem:", e)
        except OSError as e:
            print(f"OSError: {e}")


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

    def run(self):
        global debug
        while True:
            print("Iniciando servidor NMS...")
            print("1 - Iniciar socket TCP")
            print("2 - Iniciar socket UDP")
            print("3 - Load new tasks")
            print("4 - Debug mode")
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
            else:
                print("Opção inválida. Tente novamente.")
        sys.exit()


# Executando o servidor NMS
if __name__ == "__main__":
    config_path = "./dataset"
    server = NMS_Server(config_path)
    server.run()