import json
import time
from AlertFlow import TCP

class Tarefa:
    def __init__(self, config_path):
        self.config_path = config_path
        self.tasks = []
        self.load_file()

    # Carrega, interpreta e armazena as informações das tarefas e dispositivos
    # a partir do arquivo JSON de configuração
    def load_file(self):
        with open(self.config_path, 'r') as file:
            config = json.load(file)

        # Caso onde "Task" é um dicionário único
        task_data = config['Task']
        
        task_id = task_data['task_id']
        frequency = task_data['frequency']
        devices = []
        
        for device_data in task_data['devices']:
            device_id = device_data['device_id']
            device_metrics = device_data['device_metrics']
            link_metrics = device_data['link_metrics']
            alertflow_conditions = device_data['link_metrics'].get('alertflow_conditions', {})

            device = {
                'device_id': device_id,
                'device_metrics': device_metrics,
                'link_metrics': link_metrics,
                'alertflow_conditions': alertflow_conditions
            }
            devices.append(device)

        task = {
            'task_id': task_id,
            'frequency': frequency,
            'devices': devices
        }
        self.tasks.append(task)


    # Para cada tarefa, cria um processo de monitorização com a frequência definida
    def start_monitoring(self):
        for task in self.tasks:
            frequency = task['frequency']
            devices = task['devices']
            print(f"Iniciando a tarefa {task['task_id']} com frequência de {frequency} segundos")
            
            while True:
                for device in devices:
                    self.monitor_device(device)
                time.sleep(frequency)

    # Realiza a coleta de métricas do dispositivo e verifica as condições de alerta
    def monitor_device(self, device):
        device_id = device['device_id']
        device_metrics = device['device_metrics']
        alertflow_conditions = device['alertflow_conditions']

        # Verificação de uso de CPU
        cpu_usage = self.get_device_cpu_usage(device_id)
        if cpu_usage > alertflow_conditions['cpu_usage']:
            TCP.trigger_alert(device_id, "CPU usage exceeded", cpu_usage)

        # Verificação de uso de RAM
        ram_usage = self.get_device_ram_usage(device_id)
        if ram_usage > alertflow_conditions['ram_usage']:
            TCP.trigger_alert(device_id, "RAM usage exceeded", ram_usage)

        # Verificação de pacotes por segundo nas interfaces
        for interface in device_metrics['interface_stats']:
            packets_per_second = self.get_interface_packet_rate(device_id, interface)
            if packets_per_second > alertflow_conditions['interface_stats']:
                TCP.trigger_alert(device_id, f"Packet rate on {interface} exceeded", packets_per_second)

        # Verificação de perda de pacotes
        packet_loss = self.get_link_packet_loss(device_id)
        if packet_loss > alertflow_conditions['packet_loss']:
            TCP.trigger_alert(device_id, "Packet loss exceeded", packet_loss)

        # Verificação de jitter
        jitter = self.get_link_jitter(device_id)
        if jitter > alertflow_conditions['jitter']:
            TCP.trigger_alert(device_id, "Jitter exceeded", jitter)

    # Implementações simuladas para coleta das métricas --------------------------------------
    def get_device_cpu_usage(self, device_id):
        return 70

    def get_device_ram_usage(self, device_id):
        return 89

    def get_interface_packet_rate(self, device_id, interface):
        return 1850

    def get_link_packet_loss(self, device_id):
        return 250

    def get_link_jitter(self, device_id):
        return 920
    
    def get_link_latency(self, device_id):
        return 123

    def get_bandwidth(self, device_id):
        return 29