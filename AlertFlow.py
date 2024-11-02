import struct
import socket

# Tipos de mensagem:
#   - 1) Mensagem de Alerta              -> Feito   
#   - 2) Mensagem de Status de Interface -> Por Fazer
#   - 3) Mensagem de Latência            -> Por fazer
#   - 4) Mensagem de Coleta de Métricas  -> Por fazer
#   - 5) Mensagem de Confirmação (ACK)   -> Por fazer
#   - 6) Mensagem de Erro                -> Por fazer

class TCP:
    def __init__(self, tipo, identificador, dados):
        self.tipo = tipo                    
        self.identificador = identificador  # ID do NMS_Agent
        self.dados = dados.encode('utf-8')  # Conteúdo da mensagem codificado para TCP
        self.tamanho_dados = len(self.dados)

    # Formata a mensagem como um dicionário para visualização, se necessário
    def AlertFlow_Format(self):
        return {
            'tipo': self.tipo,
            'identificador': self.identificador,
            'tamanho_dados': self.tamanho_dados,
            'dados': self.dados.decode('utf-8'),
        }

    # Serialização para TCP
    def serialize_tcp(self):
        tamanho_dados = len(self.dados)
        formato = f'!B H H {tamanho_dados}s'
        return struct.pack(formato, self.tipo, self.identificador, self.tamanho_dados, self.dados)

    @staticmethod
    def deserialize_tcp(mensagem_binaria):
        tipo, identificador, tamanho_dados = struct.unpack('!B H H', mensagem_binaria[:5])
        dados = struct.unpack(f'{tamanho_dados}s', mensagem_binaria[5:])[0].decode('utf-8')
        return tipo, identificador, dados

    # Envio de mensagem TCP
    def send_message(self, endereco, porta):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((endereco, porta))
                mensagem_binaria = self.serialize_tcp()
                sock.sendall(mensagem_binaria)
                print("Alerta enviado com sucesso")
        except Exception as e:
            print(f"Erro ao enviar alerta TCP: {e}")

    # --------------------------------- Mensagens ----------------------------------------------------

    # Mensagem de alerta (tipo 1)
    @classmethod
    def trigger_alert(self, device_id, alert_type, current_value):
        # Envia um alerta via AlertFlow (TCP) quando uma condição é ultrapassada
        alert_data = f"Alert: {alert_type} on {device_id}. Current value: {current_value}"
        alert_message = TCP(1, device_id, alert_data)
        alert_message.send_message(device_id,24)
