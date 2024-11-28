import socket, os, glob, json, struct, threading
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
        self.tasks = self.load_tasks_from_json()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.upd_started = False
    # Lê todos os arquivos JSON na pasta de configurações
    def load_tasks_from_json(self):
        json_files = glob.glob(os.path.join(self.config_path, '*.json'))
        tarefas = []
        for json_file in json_files:
            print(f"Lendo configuração de: {json_file}")
            tarefa = Tarefa(config_path=json_file)  # A instância de Tarefa já chama o load_file
            tarefas.append(tarefa)
        return tarefas


    # Distribui as tarefas para os NMS_Agents via UDP
    def distribute_tasks(self,devices_task_sent):
        if not self.tasks:
            print("Nenhuma tarefa carregada para distribuição.")
            return

        for tarefa in self.tasks:
            task_id = tarefa.tasks[0]['task_id']
            frequency = tarefa.tasks[0]['frequency']
            devices = tarefa.tasks[0]['devices']
            debug_print(f"[DEBUG - Servidor] Iniciando distribuição da tarefa {task_id}")
            
            for device in devices:
                device_id = device.get('device_id')
                if device_id in devices_task_sent:
                    debug_print(f"[DEBUG - Servidor] Tarefa {task_id} já enviada para o dispositivo {device_id}.")
                    continue
                if device_id not in self.agents:
                    debug_print(f"[DEBUG - Servidor] Dispositivo {device_id} não encontrado na lista de agentes.")
                    return False
                devices_task_sent.append(device_id)
                debug_print(f"[DEBUG - Servidor] Distribuindo tarefa {task_id} para o dispositivo {device_id}")
                agent_ip, agent_port = self.agents.get(device_id)
                debug_print(f"[DEBUG - Servidor] Preparando envio para o agente {device_id} no IP {agent_ip} e porta {agent_port}")

                # Dados específicos do dispositivo
                device_specific_data = device
        
                serialized_task = json.dumps(device_specific_data, separators=(',', ':')).encode('utf-8')
                print(f"[IP]: {agent_ip}, [PORT]: {agent_port}")
                # Criar e enviar a mensagem de tarefa para o dispositivo
                task_message = UDP(2, serialized_task, identificador=device_id, sequencia=1, endereco=agent_ip, porta=agent_port, socket = self.socket)
                if task_message.send_task():
                    print(f"Tarefa {task_id} enviada para o dispositivo {device_id} no endereço {agent_ip}:{agent_port} com sucesso.")
                else:
                    print(f"Falha ao enviar a tarefa {task_id} para o dispositivo {device_id}. Nenhum ACK recebido após várias tentativas.")
                return

    def initialize_tasks(self,devices_task_sent=[]):
        devices_task_sent = devices_task_sent
        self.load_tasks_from_json()
        sucess = self.distribute_tasks(devices_task_sent)
        if not sucess:
            print("Falha ao distribuir tarefas. Tentando novamente...")
            self.start_udp_server(devices_task_sent)
        # Inicia o monitoramento de todas as tarefas
        #for task in self.tasks:
        #    task.start_monitoring()
        print("Monitoramento iniciado para todas as tarefas.")

    def start_udp_server(self,devices_task_sent=[]):
        # Configura o servidor UDP para comunicação com os NMS_Agents
        print("Servidor UDP esperando por conexões...")

        while True:
            try:
                msg, client_address = self.socket.recvfrom(1024)
                if not msg:
                    print("Mensagem vazia recebida. Continuando...")
                    continue

                print(f"Mensagem recebida de {client_address}")

                # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                sequencia, identificador, dados = UDP.desserialize(msg)
                debug_print(f"[DEBUG - dados udp] Dados desserializados - Sequência: {sequencia}, Identificador: {identificador}, Dados: {dados}")
                
                # Criando o ACK como uma instância UDP
                ack_message = UDP(tipo=99, dados="", identificador=identificador, sequencia=sequencia, endereco=client_address[0], 
                                    porta=client_address[1], socket=self.socket)
                ack_message.send_ack()

                # Guardar ip do agente que acabou de se ligar
                self.agents[identificador] = (client_address[0], client_address[1])
                debug_print(f"[DEBUG - agentes] Agentes registrados no servidor: {self.agents}")

                self.initialize_tasks(devices_task_sent)
                
            except struct.error as e:
                print("Erro ao desserializar a mensagem:", e)

    # Função para tratar a conexão de um cliente em uma thread separada.
    def handle_client_connection(conn, addr):
        debug_print(f"Conexão iniciada com {addr}")
        try:
            while True:
                msg = conn.recv(1024)
                if not msg:
                    break  # Conexão encerrada pelo cliente
                alert_type, device_id, current_value = TCP.deserialize_tcp(msg)
                debug_print(f"Alerta recebido do dispositivo {device_id}: {alert_type}, Valor atual: {current_value}")
        except Exception as e:
            debug_print(f"Erro na conexão com {addr}: {e}")
        finally:
            debug_print(f"Conexão encerrada com {addr}")
            conn.close()

    # Configura o servidor TCP para receber alertas críticos dos NMS_Agents.
    # Lida com múltiplas conexões utilizando threads.
    def start_tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            LOCAL_ADR = "10.0.5.10"
            PORT = 9000
            server_socket.bind((LOCAL_ADR, PORT))
            server_socket.listen(5)

            debug_print("Servidor TCP esperando por conexões de alertas...")

            while True:
                try:
                    # Aceita conexões de clientes
                    conn, addr = server_socket.accept()

                    # Cria uma thread para tratar a conexão do cliente
                    client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr), daemon=True)
                    client_thread.start()

                    debug_print(f"Thread criada para conexão com {addr}")
                except KeyboardInterrupt:
                    debug_print("Servidor interrompido pelo usuário.")
                    break
                except Exception as e:
                    debug_print(f"Erro no servidor: {e}")

    def run(self):
        global debug
        LOCAL_ADR = "10.0.5.10"
        self.socket.bind((LOCAL_ADR, 5000))
        while True:
            print("Iniciando servidor NMS...")
            print("1 - Iniciar socket TCP")
            print("2 - Iniciar socket UDP")
            print("3 - Distribuir tarefas")
            print("4 - Debug mode")
            print("0 - Sair")
            option = input("Digite a opção desejada: ")
            if option == "0":
                break
            elif option == "1":
                self.start_tcp_server()
            elif option == "2":
                self.start_udp_server()
            elif option == "3":
                self.initialize_tasks()
            elif option == "4":
                debug = True
                print("Debug mode ativado.")
            else:
                print("Opção inválida. Tente novamente.")


# Executando o servidor NMS
if __name__ == "__main__":

    config_path = "./dataset"
    server = NMS_Server(config_path)
    server.run()