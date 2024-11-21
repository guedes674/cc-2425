import socket, os, glob, json, struct
from AlertFlow import TCP
from NetTask import UDP
from Tarefa import Tarefa

class NMS_Server:
    def __init__(self, config_path):
        self.config_path = config_path
        self.agents = {}  # Dicionário onde cada chave é o device_id e o valor é o endereço IP/porta do agente
        self.tasks = self.load_tasks_from_json()


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
    def distribute_tasks(self):
        if not self.tasks:
            print("Nenhuma tarefa carregada para distribuição.")
            return

        for tarefa in self.tasks:
            task_id = tarefa.tasks[0]['task_id']

            for device in tarefa.tasks[0]['devices']:
                device_id = device['device_id']
                
                if device_id in self.agents:
                    agent_ip, agent_port = self.agents[device_id]

                    # Dados específicos do dispositivo
                    device_specific_data = {
                        "task_id": task_id,
                        "device_id": device_id,
                        "device_metrics": device.get("device_metrics"),
                        "link_metrics": device.get("link_metrics"),
                        "alertflow_conditions": device.get("alertflow_conditions")
                    }
                    
                    serialized_task = json.dumps(device_specific_data, separators=(',', ':')).encode('utf-8')  

                    print(f"[IP]: {agent_ip}, [PORT]: {agent_port}")
                    print(f"[TASK]: {serialized_task}")

                    # Criar e enviar a mensagem de tarefa para o dispositivo
                    task_message = UDP(2, serialized_task, identificador=device_id, sequencia=1)
                    if task_message.send_task(serialized_task, agent_ip, agent_port):
                        print(f"Tarefa {task_id} enviada para o dispositivo {device_id} no endereço {agent_ip}:{agent_port} com sucesso.")
                    else:
                        print(f"Falha ao enviar a tarefa {task_id} para o dispositivo {device_id}. Nenhum ACK recebido após várias tentativas.")
            
                else:
                    print(f"Agente para o dispositivo {device_id} não encontrado. Tarefa {task_id} não enviada.")

    def initialize_tasks(self):
        self.load_tasks_from_json()
        self.distribute_tasks()
        
        # Inicia o monitoramento de todas as tarefas
        for task in self.tasks:
            task.start_monitoring()
        print("Monitoramento iniciado para todas as tarefas.")

    def start_udp_server(self):
        # Configura o servidor UDP para comunicação com os NMS_Agents
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            LOCAL_ADR = "10.0.5.10"
            server_socket.bind((LOCAL_ADR, 5000))
        
            print("Servidor UDP esperando por conexões...")

            while True:
                try:
                    msg, client_address = server_socket.recvfrom(1024)
                    if not msg:
                        print("Mensagem vazia recebida. Continuando...")
                        continue  # Ignora pacotes vazios e continua esperando

                    print(f"Mensagem recebida de {client_address}")

                    # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                    sequencia, identificador, dados = UDP.desserialize(msg)
                    print(f"Dados desserializados - Sequência: {sequencia}, Identificador: {identificador}, Dados: {dados}")

                    # Criando o ACK como uma instância UDP
                    ack_message = UDP(tipo=99, dados="", identificador=identificador, sequencia=sequencia)
                    ack_message.send_ack(client_address[0], client_address[1])

                    # Guardar ip do agente que acabou de se ligar
                    self.agents[identificador] = (client_address[0], client_address[1])
                    print("Agentes registrados no servidor:", self.agents)

                    
                    self.initialize_tasks()

                except struct.error as e:
                    print("Erro ao desserializar a mensagem:", e)

    def start_tcp_server(self):
        # Configura o servidor TCP para receber alertas críticos dos NMS_Agents
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            LOCAL_ADR = "10.0.5.10"
            server_socket.bind((LOCAL_ADR, 9000))
            server_socket.listen(5)

            print("Servidor TCP esperando por conexões de alertas...")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Conectado por {addr}")
                    msg = conn.recv(1024)
                    if msg:
                        alert_type, device_id, current_value = TCP.deserialize_tcp(msg)
                        print(f"Alerta recebido do dispositivo {device_id}: {alert_type}, Valor atual: {current_value}")

    def run(self):
        self.start_udp_server()

# Executando o servidor NMS
if __name__ == "__main__":
    config_path = "./Tarefas"
    server = NMS_Server(config_path)
    server.run()
