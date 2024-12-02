import struct, socket

class TCP:
    def __init__(self, tipo, dados, identificador, endereco, porta, socket=None):
        self.tipo = tipo                    
        self.dados = dados.encode('utf-8')  # Conteúdo da mensagem codificado para TCP
        self.tamanho_dados = len(self.dados)
        self.identificador = identificador  # ID do NMS_Agent
        self.endereco = endereco            # Endereço do servidor
        self.porta = porta                  # Porta do servidor
        self.socket = socket if socket else self.create_socket()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.endereco, self.porta))
        print(f"Conexão estabelecida com {self.endereco}:{self.porta}")
        return sock

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
            # Serializa a mensagem e a envia
            mensagem_binaria = self.serialize_tcp()
            self.socket.sendall(mensagem_binaria)
            print("Mensagem enviada com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")

    # --------------------------------- Mensagens ----------------------------------------------------

    # Mensagem de alerta (tipo 2)
    @staticmethod
    def trigger_alert(device_id, alert_type, current_value, server_address, server_port):
        # Envia um alerta via AlertFlow (TCP) quando uma condição é ultrapassada
        alert_data = f"Alert: {alert_type} on {device_id}. Current value: {current_value}"
        alert_message = TCP(
            tipo=2,
            dados=alert_data,
            identificador=device_id,
            endereco=server_address,
            porta=server_port
        )
        alert_message.send_message()

    # Mensagem de status interface (tipo 3)
    @staticmethod
    def trigger_status_interface(device_id, server_address, server_port):
        status = self.get_device_interface_stats(device_id)
        status_data = f"Status: {status} on {device_id}"
        status_message = TCP(
            tipo=3, 
            dados=status_data, 
            identificador=device_id,
            endereco=server_address, 
            porta=server_port
        )
        status_message.send_message()

    # Mensagem de latência (ping) (tipo 4)
    @staticmethod
    def trigger_latency(device_id, server_address, server_port):
        latency = self.get_link_band_latency(device_id)
        latency_data = f"Latency: {latency} on {device_id}"
        latency_message = TCP(
            tipo=4, 
            dados=latency_data,
            identificador=device_id,
            endereco=server_address,
            porta=server_port
            )
        latency_message.send_message()

    @staticmethod
    def trigger_metrics_collection(device_id, metrics_type, metrics_data, server_address, server_port):
        metrics_data_str = f"Metrics {metrics_type} on {device_id}: {metrics_data}"
        metrics_message = TCP(
            tipo=5,
            dados=metrics_data_str,
            identificador=device_id,
            endereco=server_address,
            porta=server_port
        )
        metrics_message.send_message()

    @staticmethod
    def trigger_error(device_id, error_message, server_address, server_port):
        error_data = f"Error on {device_id}: {error_message}"
        error_message = TCP(
            tipo=6,
            dados=error_data,
            identificador=device_id,
            endereco=server_address,
            porta=server_port
        )
        error_message.send_message()

    @staticmethod
    def trigger_acknowledgment(device_id, ack_message, server_address, server_port):
        ack_data = f"ACK from {device_id}: {ack_message}"
        ack_message = TCP(
            tipo=7,
            dados=ack_data,
            identificador=device_id,
            endereco=server_address,
            porta=server_port
        )
        ack_message.send_message()