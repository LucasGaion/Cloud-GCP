import datetime
import openpyxl
from google.cloud import asset_v1
from google.cloud import compute_v1
from google.cloud import monitoring_v3

# Defina a lista de projetos
projects = [
    'shared-project-fca',
    'non-prod-project-fca',
    'prod-project-fca',
    'sap-shared-sa',
    'sap-nonprod-sa',
    'sap-prod-sa',
    'banco-fidis-prod',
    'banco-fidis-nonprod'
]

# Cria uma instância do cliente Asset do GCP
client = asset_v1.AssetServiceClient()

# Cria uma instância do cliente Compute Engine do GCP
compute_client = compute_v1.InstancesClient()

# Cria uma lista para armazenar os dados dos servidores com saída para a Internet
servers_with_internet = []

# Coleta informações sobre os servidores em cada projeto
print("\nINICIANDO O INVENTÁRIO\n")
for project in projects:
    print("Coletando servidores do projeto:", project)

    # Configura a solicitação de pesquisa de recursos
    parent = f"projects/{project}"
    asset_types = ['compute.googleapis.com/Instance']

    # Cria uma mensagem de requisição de pesquisa de recursos
    request = asset_v1.SearchAllResourcesRequest(
        scope=parent,
        asset_types=asset_types
    )

    # Faz a pesquisa de recursos
    try:
        response = client.search_all_resources(request)
    except Exception as e:
        print(f"Erro ao buscar recursos no projeto {project}: {e}")
        continue  # Pular para a próxima iteração

    # Itera sobre os recursos retornados
    for resource in response:
        try:
            # Obtém informações da instância da VM
            vm_name = resource.name.split('/')[-1]
            vm_zone = resource.location.split('/')[-1]

            # Usa a API Compute Engine para obter informações da instância
            vm_instance = compute_client.get(project=project, zone=vm_zone, instance=vm_name)

            # Usa a API de Monitoramento para obter métricas de rede
            client_monitoring = monitoring_v3.MetricServiceClient()
            project_name = f"projects/{project}"
            instance_id = f"instance_id/{vm_instance.id}"

            # Define o intervalo de tempo para a consulta da métrica
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(minutes=5)  # Você pode ajustar o intervalo de tempo conforme necessário

            # Consulta para contagens de bytes enviados e recebidos
            sent_bytes_query = 'compute.googleapis.com/instance/network/sent_bytes_count'
            received_bytes_query = 'compute.googleapis.com/instance/network/received_bytes_count'

            sent_bytes = client_monitoring.list_time_series(
                name=project_name,
                filter=f'resource.type=gce_instance AND resource.labels.instance_id="{instance_id}" AND metric.type="{sent_bytes_query}"',
                interval=monitoring_v3.TimeInterval(
                    start_time=start_time,
                    end_time=end_time,
                ),
            )
            received_bytes = client_monitoring.list_time_series(
                name=project_name,
                filter=f'resource.type=gce_instance AND resource.labels.instance_id="{instance_id}" AND metric.type="{received_bytes_query}"',
                interval=monitoring_v3.TimeInterval(
                    start_time=start_time,
                    end_time=end_time,
                ),
            )

        except Exception as e:
            print(f"Erro ao processar {vm_name} no projeto {project}: {e}")
            continue  # Pular para a próxima iteração

        # Processa e adiciona dados das métricas de rede ao dicionário de dados existente
        sent_bytes_count = sum(point.value.int64_value for series in sent_bytes for point in series.points)
        received_bytes_count = sum(point.value.int64_value for series in received_bytes for point in series.points)

        # Converta bytes para KiB
        sent_kib_per_sec = sent_bytes_count / 1024
        received_kib_per_sec = received_bytes_count / 1024

        # Adicione prints para visualizar as métricas obtidas
        print(f"Instance: {vm_name}")
        print(f"Sent Bytes Count: {sent_bytes_count} B/s")
        print(f"Received Bytes Count: {received_bytes_count} B/s")
        print(f"Sent KiB/s: {sent_kib_per_sec:.3f} KiB/s")
        print(f"Received KiB/s: {received_kib_per_sec:.3f} KiB/s")
        print(".")

        data = {
            'Project': project,
            'Instance': vm_name,
            'Sent KiB/s': f"{sent_kib_per_sec:.3f} KiB/s",
            'Received KiB/s': f"{received_kib_per_sec:.3f} KiB/s"
        }

        servers_with_internet.append(data)

# Obtém o nome do arquivo com base na data atual
current_date = datetime.datetime.now().strftime("%B-%Y")
filename = f"ServersNetworkMetrics-{current_date}.xlsx"

# Salva o arquivo XLSX
workbook = openpyxl.Workbook()
worksheet = workbook.active
headers = ['Project', 'Instance', 'Sent KiB/s', 'Received KiB/s']
worksheet.append(headers)

for server_data in servers_with_internet:
    data = [
        server_data['Project'],
        server_data['Instance'],
        server_data.get('Sent KiB/s', 'N/A'),
        server_data.get('Received KiB/s', 'N/A'),
    ]
    worksheet.append(data)

# Salva o arquivo XLSX
workbook.save(filename)
print("Arquivo", filename, "salvo com sucesso!")
