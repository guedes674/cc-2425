import json
import time
from AlertFlow import TCP

class Tarefa:
    def __init__(self, config_path,tasks_loaded):
        self.config_path = config_path
        self.tasks = []
        self.dict = {}
        self.tasks_loaded = tasks_loaded
        self.load_files()

    # Carrega, interpreta e armazena as informações das tarefas e dispositivos
    # a partir do arquivo JSON de configuração

    def load_files(self):
        for file in self.config_path:
            self.load_file(file)

    def load_file(self,file):
        with open(file, 'r') as file:
            config = json.load(file)
        # Caso onde "Task" é um dicionário único
        
        task_data = config['task']
        if task_data['task_id'] not in self.tasks_loaded:
            task_id = task_data['task_id']
            self.tasks.append(task_id)
            frequency = task_data['frequency']

            for device_data in task_data['devices']:
                device_id = device_data['device_id']
                device_metrics = device_data['device_metrics']
                link_metrics = device_data['link_metrics']
                alertflow_conditions = device_data['alertflow_conditions']

                device = {
                    'frequency': frequency,
                    'device_metrics': device_metrics,
                    'link_metrics': link_metrics,
                    'alertflow_conditions': alertflow_conditions
                }

                t = tuple((task_id, device))
                device_list = self.dict.get(device_id)
                if device_list:
                    self.dict[device_id].append(t)
                    self.dict[device_id] = sorted(self.dict[device_id], key=lambda x: x[0])
                else :
                    tuplelist = [t]
                    self.dict[device_id] = tuplelist
        else : 
            print(f"Tarefa {task_data['task_id']} já foi carregada anteriormente.")

    # Para cada tarefa, cria um processo de monitorização com a frequência definida
    def start_monitoring(self,tarefas):
        for task in tarefas:
            frequency = task['frequency']
            devices = task['devices']
            print(f"Iniciando a tarefa {task['task_id']} com frequência de {frequency} segundos")
            
            while True:
                for device in devices:
                    self.monitor_device(device)
                time.sleep(frequency)
        return self.dict

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