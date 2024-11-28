import socket
import struct 
import time

class UDP:
    def __init__(self, tipo, dados, identificador=None, sequencia=None, endereco=None, porta=None, socket=None):
        self.tipo = tipo                         # Tipo de mensagem (por exemplo, 'register', 'colect', 'alert')
        self.dados = dados.encode('utf-8') if isinstance(dados, str) else dados      # Conteúdo da mensagem
        self.identificador = identificador       # ID do NMS_Agent
        self.sequencia = sequencia               # Número de sequência para NetTask (UDP)
        self.endereco = endereco                 # Endereço do servidor
        self.porta = porta                       # Porta do servidor
        self.socket = socket if socket else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Reutiliza o socket, se disponível
    # --------------------------- UDP ---------------------------

    # Antes de enviar um pacote, devemos serializá-lo (mudar para formato binário)
    def serialize(self):
        id_bytes = self.identificador.encode('utf-8')  
        tamanho_identificador = len(id_bytes)
        tamanho_dados = len(self.dados)
        formato = f'!I H H {tamanho_identificador}s {tamanho_dados}s'  # Formato ajustado para incluir identificador como string
        return struct.pack(formato, self.sequencia, tamanho_identificador, tamanho_dados, id_bytes, self.dados)

    # Uma vez que a mensagem esteja em formato binário, é necessário 'desformatá-la'
    @staticmethod
    def desserialize(mensagem_binaria):
        try:
            # Primeiro extrai os tamanhos dos campos
            sequencia, tamanho_identificador, tamanho_dados = struct.unpack('!I H H', mensagem_binaria[:8])
            
            # Define o formato dinâmico para o conteúdo com base nos tamanhos extraídos
            formato = f'{tamanho_identificador}s {tamanho_dados}s'
            id_bytes, dados_bytes = struct.unpack(formato, mensagem_binaria[8:])
            
            # Decodifica os bytes para strings
            identificador = id_bytes.decode('utf-8') if id_bytes else "default_id"
            dados = dados_bytes.decode('utf-8') if dados_bytes else ""
            
            return sequencia, identificador, dados
        except Exception as e:
            print(f"Erro ao desserializar a mensagem: {e}")
            return None, None, None


    # Enviar uma mensagem UDP com controle de fluxo e esperar pelo ACK
    def send_message(self, max_retries=3, timeout=2, delay=0.5):
        # Verifique se os valores estão corretos
        if self.endereco is None or self.porta is None:
            print(f"[ERRO - send_message] Endereço ou porta não configurados corretamente: {self.endereco}, {self.porta}")
            return False

        # Usa o socket existente, configurando o timeout uma vez
        if not self.socket.gettimeout():
            self.socket.settimeout(timeout)
        
        mensagem_binaria = self.serialize()
        print(f"[DEBUG - send_message] Enviando mensagem para {self.endereco}:{self.porta} - Tipo: {self.tipo}, Sequência: {self.sequencia}")

        if self.tipo == 99:  # Envio de ACK sem esperar
            self.socket.sendto(mensagem_binaria, (self.endereco, self.porta))
            print("[ACK] Enviado sem esperar confirmação")
            return True

        # Implementação de reenvio para mensagens que necessitam de confirmação
        tentativas = 0
        ack_recebido = False
        while tentativas < max_retries and not ack_recebido:
            self.socket.sendto(mensagem_binaria, (self.endereco, self.porta))
            print(f"[DEBUG - send_message] Mensagem enviada, aguardando ACK (tentativa {tentativas + 1})")
            print(self.socket)
            try:
                ack_mensagem, _ = self.socket.recvfrom(1024)
                ack_sequencia, ack_identificador, _ = UDP.desserialize(ack_mensagem)
                if ack_sequencia == self.sequencia and ack_identificador == self.identificador:
                    ack_recebido = True
                    print("[DEBUG - send_message] ACK válido recebido")
            except socket.timeout:
                print("[ERRO - send_message] Timeout ao aguardar ACK")
                tentativas += 1
                time.sleep(delay * (2 ** tentativas))

        if not ack_recebido:
            print("[ERRO - send_message] Falha ao receber ACK após várias tentativas")

        return ack_recebido

    # --------------------------- Mensagens ---------------------------
    # Falta estas mensagens:
    # - Registo                                   --> feito
    # - ACK                                       --> feito
    # - Envio Tarefa                              --> feito
    # - Executar testes de monitorização          --> por fazer
    # - Reportar os resultados periodicamente (?) --> por fazer

    # Mensagem de tipo 1 - Registo
    def registo(self):
        print(f"[NetTask] Registo do NMS_Agent com ID {self.identificador} no NMS_Server...")
        register_message = UDP(1, "", self.identificador, 1, self.endereco, self.porta)
        register_message.send_message()

    # Mensagem de tipo 99 - ACK
    def send_ack(self):
        print('[NetTask] Envio de ACK')
        self.send_message()

    # Mensagem de tipo 2 - Envio de Tarefa
    def send_task(self):
        print(f'[NetTask] Envio de Tarefa para {self.endereco}:{self.porta}')
        task_message = UDP(2, self.dados, self.identificador, self.sequencia, self.endereco, self.porta,self.socket)
        task_message.send_message()