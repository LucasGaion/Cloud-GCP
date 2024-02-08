import datetime
import openpyxl
from google.cloud import asset_v1

# Define a lista de projetos
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

# Cria um novo arquivo XLSX
workbook = openpyxl.Workbook()
worksheet = workbook.active

# Define os cabeçalhos das colunas
headers = [
    'Hostname', 'Name', 'Project', 'Region', 'Internal-IP', 'External-IP', 'App-Name', 'App-Id',
    'Instance-Type', 'Environment', 'Platform', 'Cost-Center', 'ITO-Provider', 'Product',
    'Business-Unit', 'DB-Engine', 'Owned-By', 'Auto-ONOFF'
]

# Adiciona os cabeçalhos à planilha
worksheet.append(headers)

# Cria uma instância do cliente Asset do GCP
client = asset_v1.AssetServiceClient()

# Coleta informações sobre os servidores em cada projeto
print("\n")
print("INICIANDO O INVENTARIO \n")
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
    response = client.search_all_resources(request)

    # Itera sobre os recursos retornados
    for resource in response:
        internal_ips = resource.additional_attributes.get('internalIPs', '')
        external_ips = resource.additional_attributes.get('externalIPs', '')

        data = [
            resource.name.split('/')[-1],  # Obtém o hostname do atributo 'name'
            resource.display_name,
            project,
            resource.location.split('/')[-1],
            ', '.join(internal_ips),
            ', '.join(external_ips),
            resource.labels.get('app-name', ''),
            resource.labels.get('app-id', ''),
            resource.additional_attributes.get('machineType', ''),
            resource.labels.get('environment', ''),
            resource.labels.get('platform', ''),
            resource.labels.get('cost-center', ''),
            resource.labels.get('ito-provider', ''),
            resource.labels.get('product', ''),
            resource.labels.get('business-unit', ''),
            resource.labels.get('db-engine', ''),
            resource.labels.get('owned-by', ''),
            resource.labels.get('auto-onoff', '')
        ]

        # Adiciona os dados à planilha
        worksheet.append(data)

# Obtém o nome do arquivo com base na data atual
current_date = datetime.datetime.now().strftime("%B-%Y")
filename = f"ServersGCP-{current_date}.xlsx"

# Salva o arquivo XLSX
workbook.save(filename)
print("Arquivo", filename, "salvo com sucesso!")
