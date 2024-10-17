import socket
import struct

def start_server():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    LOCAL_ADR = "10.0.5.10"
    server_socket.bind((LOCAL_ADR, 8080))
    server_socket.listen(1)

    print("ola")
    print("Servidor esperando por conexões...")

    conn, addr = server_socket.accept()
    print(f"Conectado por {addr}")

    while True:
        data = conn.recv(1024)
        if not data:
            break
        print(f"Recebido: {data.decode()}")
        conn.sendall(data)  # Echo de volta para o cliente

    conn.close()

start_server()

""" def send_alert(alert_id, alert_type, severity, message):
    server_address = ('localhost', 8080)
    timestamp = int(time.time())
    header = struct.pack('!I B B I H', alert_id, alert_type, severity, timestamp, 0)
    payload = message.encode()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)
        sock.sendall(header + payload)
        response = sock.recv(1024)
        print(f"Resposta do servidor: {response.decode()}")
    finally:
        sock.close() """

""" send_alert(1, 0x01, 0x01, "Erro crítico no sistema") """