import socket
import struct 
import time
import sys 
import os 
debug = True

def debug_print(message):
    if debug:
        print(message)



class UDP:
    def __init__(self, dados, identificador=None, tipo=None, endereco=None, porta=None, socket=None):
        self.dados = dados.encode('utf-8') if isinstance(dados, str) else dados      # Conteúdo da mensagem
        self.identificador = identificador       # ID do NMS_Agent
        self.tipo = tipo                         # O tipo da mensagem (1 - Envio de Metricas,2 - Envio de mensagem normal,80 - ACK pedir porta tcp,88 - ACK para avisar que nao ha porta iperf, 96 - ACK de iperf porta, 97 - ACK de metricas, 98 - ACK de tarefa, 99 - ACK de registo)
        self.endereco = endereco                 # Endereço do servidor
        self.porta = porta                       # Porta do servidor
        self.socket = socket if socket else self.create_socket()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect((self.endereco, self.porta))
        print(f"Conexão estabelecida com {self.endereco}:{self.porta}")
        return sock

    # --------------------------- UDP ---------------------------

    # Antes de enviar um pacote, devemos serializá-lo (mudar para formato binário)
    def serialize(self):
        id_bytes = self.identificador.encode('utf-8')  
        tamanho_identificador = len(id_bytes)
        tamanho_dados = len(self.dados)
        formato = f'!I H H {tamanho_identificador}s {tamanho_dados}s'  # Formato ajustado para incluir identificador como string
        return struct.pack(formato, self.tipo, tamanho_identificador, tamanho_dados, id_bytes, self.dados)

    # Uma vez que a mensagem esteja em formato binário, é necessário 'desformatá-la'
    @staticmethod
    def desserialize(mensagem_binaria):
        try:
            # Primeiro extrai os tamanhos dos campos
            tipo, tamanho_identificador, tamanho_dados = struct.unpack('!I H H', mensagem_binaria[:8])
            
            # Define o formato dinâmico para o conteúdo com base nos tamanhos extraídos
            formato = f'{tamanho_identificador}s {tamanho_dados}s'
            id_bytes, dados_bytes = struct.unpack(formato, mensagem_binaria[8:])
            
            # Decodifica os bytes para strings
            identificador = id_bytes.decode('utf-8') if id_bytes else "default_id"
            dados = dados_bytes.decode('utf-8') if dados_bytes else ""
            
            return tipo, identificador, dados
        except Exception as e:
            print(f"Erro ao desserializar a mensagem: {e}")
            return None, None, None


    # Enviar uma mensagem UDP com controle de fluxo e esperar pelo ACK
    def send_message(self, max_retries=3, timeout=2, delay=0.5):
        # Verifique se os valores estão corretos
        if self.endereco is None or self.porta is None:
            debug_print(f"[ERRO - send_message] Endereço ou porta não configurados corretamente: {self.endereco}, {self.porta}")
            return False

        mensagem_binaria = self.serialize()
        debug_print(f"[DEBUG - send_message] Enviando mensagem para {self.endereco}:{self.porta} - Tipo: {self.tipo}")

        if self.tipo ==1 or self.tipo == 2:
            # Implementação de reenvio para mensagens que necessitam de confirmação
            tentativas = 0
            ack_recebido = False
            while tentativas < max_retries and not ack_recebido:
                self.socket.sendto(mensagem_binaria, (self.endereco, self.porta))
                debug_print(f"[DEBUG - send_message] Mensagem enviada, aguardando ACK (tentativa {tentativas + 1})")
                try:
                    self.socket.settimeout(timeout)
                    ack_mensagem, _ = self.socket.recvfrom(1024)
                    ack_tipo, ack_identificador, _ = UDP.desserialize(ack_mensagem)
                    ack_recebido = True
                    
                    debug_print("[DEBUG - send_message] ACK válido recebido")
                except socket.timeout:
                    debug_print("[ERRO - send_message] Timeout ao aguardar ACK")
                    tentativas += 1
                    time.sleep(delay * (2 ** tentativas))
            self.socket.settimeout(None)
            if not ack_recebido:
                debug_print("[ERRO - send_message] Falha ao receber ACK após várias tentativas")

            return ack_recebido
        else:
            self.socket.sendto(mensagem_binaria, (self.endereco, self.porta))
            print(f"[ACK] Enviado ack {self.tipo}")
            return True
    # --------------------------- Mensagens ---------------------------
    # Falta estas mensagens:
    # - Registo                                   --> feito
    # - ACK                                       --> feito
    # - Envio Tarefa                              --> feito
    # - Executar testes de monitorização          --> por fazer
    # - Reportar os resultados periodicamente (?) --> por fazer

    # Mensagem de registo
    def registo(self):
        debug_print(f"[NetTask] Registo do NMS_Agent com ID {self.identificador} no NMS_Server...")
        register_message = UDP("", self.identificador, 1, self.endereco, self.porta)
        register_message.send_message()

    # Mensagem de ACK
    def send_ack(self):
        debug_print('[NetTask] Envio de ACK')
        self.send_message()

    # Mensagem de envio de Tarefa
    def send_task(self):
        debug_print(f'[NetTask] Envio de Tarefa para {self.endereco}:{self.porta}')
        task_message = UDP(self.dados, self.identificador, self.tipo, self.endereco, self.porta,self.socket)
        task_message.send_message()
        
def send_ack_get_reply(id, tipo, endereco, porta, socket, timeout=5):
    message = UDP("", id, tipo, endereco, porta, socket)
    message.send_message()
    socket.settimeout(timeout)
    ack_recebido = False
    while not ack_recebido:
        try:
            ack_mensagem, _ = socket.recvfrom(1024)
            ack_tipo, _, _ = UDP.desserialize(ack_mensagem)
            if ack_tipo == tipo:
                debug_print(f"[ACK - send_ack_get_reply] Recebido ack {tipo}")
                ack_recebido = True
            else:
                debug_print(f"[ERRO - send_ack_get_reply] ACK recebido não corresponde ao esperado")
                message.send_message()
        except socket.timeout:
            debug_print(f"[ERRO - send_ack_get_reply] Timeout ao aguardar ACK {tipo}")
            #send_ack_get_reply(id, tipo, endereco, porta, socket)
            #return
        except Exception as e:
            print(f"[ERRO - receive_task] Falha ao receber mensagem: {e}")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
    socket.settimeout(None)