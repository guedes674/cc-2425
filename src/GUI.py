import tkinter as tk
from tkinter import ttk

class MetricsViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NMS Metrics Viewer")
        self.metrics_data = {}  # Estrutura para armazenar as métricas recebidas
        self.create_gui()

    def create_gui(self):
        # Título
        title = tk.Label(self.root, text="NMS Metrics Viewer", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=10, sticky="nwes")

        # Área para exibição das métricas
        self.metrics_frame = ttk.Frame(self.root)
        self.metrics_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

        # Cabeçalho da tabela
        headers = ["Client ID", "Métrica", "Valor Atual", "Estado"]
        for i, header in enumerate(headers):
            header_label = tk.Label(self.metrics_frame, text=header, font=("Arial", 12, "bold"))
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # Adiciona uma barra de rolagem
        self.canvas = tk.Canvas(self.metrics_frame)
        self.scroll_y = ttk.Scrollbar(self.metrics_frame, orient="vertical", command=self.canvas.yview)
        self.metrics_table = ttk.Frame(self.canvas)

        self.metrics_table.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.metrics_table, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.grid(row=1, column=0, columnspan=4, sticky="w")
        self.scroll_y.grid(row=1, column=4, sticky="ns")

        # Botão para atualizar métricas manualmente
        refresh_button = tk.Button(self.root, text="Atualizar Métricas", command=self.refresh_metrics)
        refresh_button.grid(row=2, column=0, columnspan=4, pady=5, sticky="ns")

    def add_metric(self, client_id, metric_name, value, state):
        row = len(self.metrics_data) + 1
        self.metrics_data[(client_id, metric_name)] = {"value": value, "state": state}

        tk.Label(self.metrics_table, text=client_id).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        tk.Label(self.metrics_table, text=metric_name).grid(row=row, column=1, padx=20, pady=5, sticky="w")
        tk.Label(self.metrics_table, text=value).grid(row=row, column=2, padx=20, pady=5, sticky="w")

        state_label = tk.Label(self.metrics_table, text=state)
        if state == "Crítico":
            state_label.config(bg="red", fg="white")
        elif state == "Atenção":
            state_label.config(bg="yellow")
        elif state == "Normal":
            state_label.config(bg="green", fg="white")
        state_label.grid(row=row, column=3, padx=40, pady=5, sticky="w")

    def refresh_metrics(self):
        """Atualiza as métricas na interface gráfica."""
        simulated_metrics = {
            "Client1": {
                "CPU Usage": {"value": "85%", "state": "Crítico"},
                "RAM Usage": {"value": "60%", "state": "Normal"},
                "Packet Loss": {"value": "5%", "state": "Atenção"}
            },
            "Client2": {
                "CPU Usage": {"value": "70%", "state": "Atenção"},
                "RAM Usage": {"value": "50%", "state": "Normal"},
                "Packet Loss": {"value": "2%", "state": "Normal"}
            }
        }

        for client_id, metrics in simulated_metrics.items():
            for metric_name, data in metrics.items():
                if (client_id, metric_name) not in self.metrics_data:
                    self.add_metric(client_id, metric_name, data["value"], data["state"])
                else:
                    # Atualiza o valor e o estado da métrica existente
                    self.metrics_data[(client_id, metric_name)]["value"] = data["value"]
                    self.metrics_data[(client_id, metric_name)]["state"] = data["state"]
                    row = list(self.metrics_data.keys()).index((client_id, metric_name)) + 1
                    self.metrics_table.grid_slaves(row=row, column=2)[0].config(text=data["value"])
                    state_label = self.metrics_table.grid_slaves(row=row, column=3)[0]
                    state_label.config(text=data["state"])
                    if data["state"] == "Crítico":
                        state_label.config(bg="red", fg="white")
                    elif data["state"] == "Atenção":
                        state_label.config(bg="yellow", fg="black")
                    elif data["state"] == "Normal":
                        state_label.config(bg="green", fg="white")

# main
metrics_viewer = MetricsViewer()

metrics_viewer.root.mainloop()