import socket, os, glob, json, struct
from AlertFlow import TCP
from NetTask import UDP
from Tarefa import Tarefa

class NMS_Server:
    def __init__(self, config_path):
        self.config_path = config_path
        self.tarefas = []

    # Lê todos os arquivos JSON na pasta de configurações
    def load_tasks_from_json(self):
        json_files = glob.glob(os.path.join(self.config_path, '*.json'))
        for json_file in json_files:
            print(f"Lendo configuração de: {json_file}")
            tarefa = Tarefa(config_path=json_file)
            self.tarefas.append(tarefa)


    # Distribui as tarefas para os NMS_Agents via UDP
    def distribute_tasks(self):
        if not self.tarefas:
            print("Nenhuma tarefa carregada para distribuição.")
            return
        
        for tarefa in self.tarefas:
            for task in tarefa.tasks:  # Acessa a lista de tarefas dentro da instância Tarefa
                serialized_task = json.dumps(task).encode('utf-8') 
                for device in task.get("devices", []):
                    device_ip = device.get('ip')  # Assegure-se de ter o IP correto
                    if device_ip:
                        self.UDP.send_message(serialized_task, device_ip, 8080)  # Envia para o IP do dispositivo
                        print(f"Tarefa enviada para o dispositivo {device['device_id']} no endereço {device_ip}.")
                    else:
                        print(f"IP não encontrado para o dispositivo {device['device_id']}.")

    # Função de teste para verificar se as tarefas foram carregadas
    def print_loaded_tasks(self):
        if not self.tarefas:
            print("Nenhuma tarefa foi carregada.")
        else:
            for idx, tarefa in enumerate(self.tarefas, start=1):
                print(f"\nTarefa {idx}:")
                for task in tarefa.tasks:
                    print(json.dumps(task, indent=4))

    def start_server(self):
        self.load_tasks_from_json()
        # self.print_loaded_tasks()
        self.distribute_tasks()
        
        # Inicia o monitoramento de todas as tarefas
        for tarefa in self.tarefas:
            tarefa.start_monitoring()
        print("Monitoramento iniciado para todas as tarefas.")

    def start_udp_server(self):
        # Configura o servidor UDP para comunicação com os NMS_Agents
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
            LOCAL_ADR = "10.0.5.10"
            server_socket.bind((LOCAL_ADR, 8080))

            print("Servidor UDP esperando por conexões...")

            while True:
                msg, client_address = server_socket.recvfrom(1024)
                if not msg:
                    break

                print(f"Mensagem recebida de {client_address}")

                # Desserializar e processar a mensagem recebida de um NMS_Agent via UDP
                try:
                    sequencia, identificador, dados = UDP.desserialize_udp(msg)
                    print(f"Dados desserializados - Sequência: {sequencia}, Identificador: {identificador}, Dados: {dados.decode('utf-8')}")

                    # Envia um ACK de volta para o cliente
                    ack_message = struct.pack('!I H', sequencia, identificador)
                    server_socket.sendto(ack_message, client_address)
                    print("ACK enviado para o cliente.")

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
        # Inicia ambos os servidores
        #from threading import Thread
        #Thread(target=self.start_udp_server).start()
        #Thread(target=self.start_tcp_server).start()
        
        self.start_server()

# Executando o servidor NMS
if __name__ == "__main__":
    config_path = "./Tarefas"
    server = NMS_Server(config_path)
    server.run()
