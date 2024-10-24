import socket
import struct 

class Mensagem:
    def __init__(self, protocolo, tipo, dados, identificador=None, sequencia=None):
        self.protocolo = protocolo  # 'NetTask' (1) ou 'AlertFlow' (0)
        self.tipo = tipo  # Tipo de mensagem (por exemplo, 'registro', 'coleta', 'alerta')
        self.dados = dados  # Conteúdo da mensagem
        self.identificador = identificador  # ID do NMS_Agent
        self.sequencia = sequencia  # Número de sequência para NetTask (UDP)

    def formatar_mensagem(self):
        # Função para formatar a mensagem para envio
        mensagem_formatada = {
            'protocolo': self.protocolo,
            'tipo': self.tipo,
            'dados': self.dados,
            'identificador': self.identificador,
            'sequencia': self.sequencia
        }
        return mensagem_formatada
    
    # --------------------------- UDP ---------------------------
    # Formato da mensagem
    def NetTask_Format(self):
        return {
            'sequencia': self.sequencia,
            'identificador': self.identificador,
            'dados': self.dados,
        }
    
    # Antes de enviar um pacote, devemos serializá-lo (mudar para formato binário)
    def serialize_udp(self):
        tamanho_dados = len(self.dados)
        formato = f'!I H H {tamanho_dados}s'  # Formato binário
        return struct.pack(formato, self.sequencia, self.identificador, tamanho_dados, self.dados)

    # Uma vez que a mensagem esteja em formato binário, é necessário 'desformatá-la'
    def desserialize_udp(mensagem_binaria):
        sequencia, identificador, tamanho_dados = struct.unpack('!I H H', mensagem_binaria[:8])
        dados = struct.unpack(f'{tamanho_dados}s', mensagem_binaria[8:])[0]
        return sequencia, identificador, dados

    # --------------------------- TCP ---------------------------
    # Formato da mensagem
    def AlertFlow_Format(self): 
        return {
            'tipo': self.tipo,
            'identificador': self.identificador,
            'dados': self.dados,
        }
    
    # Mesma coisa que em cima, mas para o TCP
    def serialize_tcp(self):
        tamanho_dados = len(self.dados)
        formato = f'!B H H {tamanho_dados}s'  # Formato binário
        return struct.pack(formato, self.tipo, self.identificador, tamanho_dados, self.dados)

    def deserialize_tcp(mensagem_binaria):
        tipo, identificador, tamanho_dados = struct.unpack('!B H H', mensagem_binaria[:5])
        dados = struct.unpack(f'{tamanho_dados}s', mensagem_binaria[5:])[0]
        return tipo, identificador, dados

