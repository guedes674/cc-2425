import socket
import struct 
import time

class UDP:
    def __init__(self, tipo, dados, identificador=None, sequencia=None):
        self.tipo = tipo                    # Tipo de mensagem (por exemplo, 'register', 'colect', 'alert')
        self.dados = dados.encode('utf-8')  # Conteúdo da mensagem
        self.identificador = identificador  # ID do NMS_Agent
        self.sequencia = sequencia          # Número de sequência para NetTask (UDP)
 
    # --------------------------- UDP ---------------------------
    
    
    # Antes de enviar um pacote, devemos serializá-lo (mudar para formato binário)
    def serialize(self):
        tamanho_dados = len(self.dados)
        formato = f'!I H H {tamanho_dados}s'  # Formato binário
        return struct.pack(formato, self.sequencia, self.identificador, tamanho_dados, self.dados)

    # Uma vez que a mensagem esteja em formato binário, é necessário 'desformatá-la'
    @staticmethod
    def desserialize(mensagem_binaria):
        sequencia, identificador, tamanho_dados = struct.unpack('!I H H', mensagem_binaria[:8])
        dados = struct.unpack(f'{tamanho_dados}s', mensagem_binaria[8:])[0]
        return sequencia, identificador, dados

    # Enviar uma mensagem UDP com controle de fluxo e esperar pelo ACK
    def send_message(self, endereco, porta, max_retries=3, timeout=2, delay=0.5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)  # Define o timeout para aguardar o ACK
        mensagem_binaria = self.serialize()  # Serializa a mensagem para binário
        
        tentativas = 0
        ack_recebido = False
        
        while tentativas < max_retries and not ack_recebido:
            print(f"Enviando tentativa {tentativas + 1}")
            sock.sendto(mensagem_binaria, (endereco, porta))  # Envia o pacote para o destinatário
            
            try:
                # Espera pelo ACK
                ack_mensagem, _ = sock.recvfrom(1024)
                ack_sequencia, ack_identificador = struct.unpack('!I H', ack_mensagem[:6])
                
                # Verifica se o ACK corresponde ao número de sequência e identificador do pacote enviado
                if ack_sequencia == self.sequencia and ack_identificador == self.identificador:
                    ack_recebido = True
                    print("ACK recebido com sucesso")
                else:
                    print("ACK incorreto ou não corresponde ao pacote enviado")
                    
            except socket.timeout:
                # Caso o ACK não seja recebido, tenta novamente
                print("Timeout ao aguardar ACK, tentando novamente...")
                tentativas += 1
            
            # Backoff exponencial no delay entre tentativas
            if not ack_recebido:
                atual_delay = delay * (2 ** tentativas)
                print(f"Aguardando {atual_delay:.2f} segundos antes de tentar novamente...")
                time.sleep(atual_delay)
        
        sock.close()
        
        if not ack_recebido:
            print("Falha ao receber ACK após várias tentativas")
        return ack_recebido
1

