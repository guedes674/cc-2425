import socket
import struct 
import time

class UDP:
    def __init__(self, tipo, dados, identificador=None, sequencia=None):
        self.tipo = tipo                         # Tipo de mensagem (por exemplo, 'register', 'colect', 'alert')
        self.dados = dados.encode('utf-8') if isinstance(dados, str) else dados      # Conteúdo da mensagem
        self.identificador = str(identificador)  # ID do NMS_Agent
        self.sequencia = sequencia               # Número de sequência para NetTask (UDP)
 
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
            dados = dados_bytes.decode('utf-8')
            
            return sequencia, identificador, dados
        except Exception as e:
            print(f"Erro ao desserializar a mensagem: {e}")
            return None, None, None


    # Enviar uma mensagem UDP com controle de fluxo e esperar pelo ACK
    def send_message(self, endereco, porta, max_retries=3, timeout=2, delay=0.5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        mensagem_binaria = self.serialize()  
        
        # Verificar se é uma mensagem de tipo ACK (tipo=99) e enviar sem esperar resposta
        if self.tipo == 99:
            sock.sendto(mensagem_binaria, (endereco, porta))
            print("[ACK] Enviado para o destinatário, sem espera de confirmação")
            sock.close()
            return True  


        tentativas = 0
        ack_recebido = False
        
        while tentativas < max_retries and not ack_recebido:
            print(f"Enviando tentativa {tentativas + 1}")
            sock.sendto(mensagem_binaria, (endereco, porta))  # Envia o pacote para o destinatário

            try:
                # Espera pelo ACK
                ack_mensagem, _ = sock.recvfrom(1024)
                ack_sequencia, ack_identificador, _ = UDP.desserialize(ack_mensagem)
                
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


    # --------------------------- Mensagens ---------------------------
    # Falta estas mensagens:
    # - Registo                                   --> feito
    # - ACK                                       --> feito
    # - Envio Tarefa                              --> feito
    # - Executar testes de monitorização          --> por fazer
    # - Reportar os resultados periodicamente (?) --> por fazer

    # Mensagem de tipo 1 - Registo
    def registo(self, endereco, porta):
        print(f"[NetTask] Registo do NMS_Agent com ID {self.identificador} no NMS_Server...")
        register_message = UDP(1, "", identificador=self.identificador, sequencia=1)
        register_message.send_message(endereco, porta)

    # Mensagem de tipo 99 - ACK
    def send_ack(self, endereco, porta):
        print('[NetTask] Envio de ACK')
        ack_message = UDP(99, "", identificador=self.identificador, sequencia=self.sequencia)
        ack_message.send_message(endereco, porta)

    # Mensagem de tipo 2 - Envio de Tarefa
    def send_task(self, dados, endereco, porta):
        print('[NetTask] Envio de Tarefa')
        task_message = UDP(2, dados, identificador=self.identificador, sequencia=self.sequencia)
        task_message.send_message(endereco, porta)
        print('oi')


