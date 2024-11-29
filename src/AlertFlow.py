import struct
import socket

# Tipos de mensagem:
#   - 1) Mensagem de Alerta              -> Feito
#   - 2) Mensagem de Status de Interface -> Por Fazer
#   - 3) Mensagem de Latência(ping)      -> Por fazer
#   - 4) Mensagem de Coleta de Métricas(ram,cpu,...)  -> Por fazer
#   - 5) Mensagem de Confirmação (ACK)   -> Por fazer
#   - 6) Mensagem de Erro                -> Por fazer

class TCP:
    def __init__(self, tipo, dados, identificador, endereco, porta, socket):
        self.tipo = tipo                    
        self.dados = dados.encode('utf-8')  # Conteúdo da mensagem codificado para TCP
        self.tamanho_dados = len(self.dados)
        self.identificador = identificador  # ID do NMS_Agent
        self.endereco = endereco            # Endereço do servidor
        self.porta = porta                  # Porta do servidor
        self.socket = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.endereco, self.porta))
            print(f"Conexão estabelecida com {self.endereco}:{self.porta}")
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            self.socket = None
    
    def disconnect(self):
        if self.socket:
            self.socket.close()
            print("Conexão TCP encerrada.")
            self.socket = None

    # Serialização para TCP
    def serialize_tcp(self):
        id_bytes = self.identificador.encode('utf-8')
        tamanho_identificador = len(id_bytes)
        tamanho_dados = len(self.dados)
        formato = f'!B H H {tamanho_identificador}s {tamanho_dados}s'
        return struct.pack(formato, self.tipo, tamanho_identificador, tamanho_dados, id_bytes, self.dados)

    @staticmethod
    def deserialize_tcp(mensagem_binaria):
        try:
            # Extrai os primeiros campos fixos: tipo, tamanho do identificador e tamanho dos dados
            tipo, tamanho_identificador, tamanho_dados = struct.unpack('!B H H', mensagem_binaria[:5])
            
            # Define o formato dinâmico com base nos tamanhos extraídos
            formato = f'{tamanho_identificador}s {tamanho_dados}s'
            
            # Extrai os bytes para o identificador e os dados
            id_bytes, dados_bytes = struct.unpack(formato, mensagem_binaria[5:])
            
            # Decodifica os bytes para strings, com verificações de vazio
            identificador = id_bytes.decode('utf-8') if id_bytes else "default_id"
            dados = dados_bytes.decode('utf-8') if dados_bytes else ""
                        
            return tipo, identificador, dados
        except Exception as e:
            print(f"Erro ao desserializar a mensagem: {e}")
            return None, None, None




    # Envio de mensagem TCP
    def send_message(self):
        try:
            # Conectar se o socket não estiver conectado
            if self.socket is None:
                self.connect()
            
            # Verifica se a conexão foi estabelecida
            if self.socket:
                mensagem_binaria = self.serialize_tcp()
                self.socket.sendall(mensagem_binaria)
                print("Mensagem enviada com sucesso.")
            else:
                print("Não foi possível enviar a mensagem: Conexão não estabelecida.")
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            self.disconnect()

    # --------------------------------- Mensagens ----------------------------------------------------


    # Mensagem de alerta (tipo 1)
    @classmethod
    def trigger_alert(self, device_id, alert_type, current_value):
        # Envia um alerta via AlertFlow (TCP) quando uma condição é ultrapassada
        alert_data = f"Alert: {alert_type} on {device_id}. Current value: {current_value}"
        alert_message = TCP(1, device_id, alert_data)
        alert_message.send_message(device_id,24)

    # Mensagem de status interface (tipo 2)
    @classmethod
    def trigger_status_interface(self, device_id):
        status = self.get_device_interface_stats(device_id)
        status_data = f"Status: {status} on {device_id}"
        status_message = TCP(1, device_id, status_data)
        status_message.send_message(device_id, 24)

    # Mensagem de latência (ping) (tipo 3)
    @classmethod 
    def trigger_latency(self,device_id):
        latency = self.get_link_band_latency(device_id)
        latency_data = f"Latency: {latency} on {device_id}"
        latency_message = TCP(1, device_id, latency_data)
        latency_message.send_message(device_id, 24)