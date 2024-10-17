import socket

def connect():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect(('10.0.5.10', 8080))
    server_socket.sendall(b"hello")

connect()

""" def send_net_task(task_id, task_type, flags, data):
    server_address = ('localhost', 12345)
    message = struct.pack('!I B B H', task_id, task_type, flags, 0) + data.encode()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(message, server_address)
    finally:
        sock.close()
 """
""" send_net_task(1, 0x01, 0x01, "Ping data") """