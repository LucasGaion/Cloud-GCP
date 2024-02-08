from google.auth import compute_engine
from googleapiclient import discovery
import csv
import time
from google.cloud import compute_v1
from google.cloud.exceptions import ClientError
from zabbix_api import ZabbixAPI
from datetime import datetime

# Função para ligar a instância GCP
def start_gcp_instance(instance, project_id, zone):
    credentials = compute_engine.Credentials()
    service = discovery.build('compute', 'v1', credentials=credentials)
    instance_name = f'projects/{project_id}/zones/{zone}/instances/{instance}'
    try:
        instance_data = service.instances().get(project=project_id, zone=zone, instance=instance).execute()
        if instance_data['status'] == 'TERMINATED':
            request = service.instances().start(project=project_id, zone=zone, instance=instance)
            print(f"Ligando instância: {instance} no projeto: {project_id}, na zona: {zone}", flush=True)
            try:
                response = request.execute()
                time.sleep(10)
                with open('instancias_ligadas.csv', 'a', newline='') as arquivo_saida:
                    csv_writer = csv.writer(arquivo_saida)
                    csv_writer.writerow([project_id, instance, instance_data["status"]])
            except Exception as e:
                print(f'Error starting instance: {e}', flush=True)
        else:
            print('Instance is not in TERMINATED state. No action required.', flush=True)
    except Exception as auth_error:
        print(f'Authentication error: {auth_error}', flush=True)

# Função principal
def main(event, context):
    result = []
    URL = 'http://18.206.216.240/zabbix'
    USERNAME = "teste.guest"
    PASSWORD = "npo@2023"
    DATA = datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        zapi = ZabbixAPI(URL, timeout=180, validate_certs=False)
        zapi.login(USERNAME, PASSWORD)
        print(f'Conectado na API do Zabbix: {zapi.api_version()}')
    except Exception as err:
        print('Falha ao acessar a API do Zabbix')
        print('Erro: {}'.format(err))

    client = compute_v1.InstancesClient()

    project_id_gce = 'teste-lucas-non-prod'
    zone_gce = 'us-central1-a'
    filter_str = "labels.auto-onoff:true AND status:TERMINATED"

    instances_gce = client.list(project=project_id_gce, zone=zone_gce)

    for instance in instances_gce:
        if instance.labels and instance.labels.get('auto-onoff') == 'true' and instance.status == 'TERMINATED':
            instance_name = instance.name
            start_gcp_instance(instance_name, project_id_gce, zone_gce)

            # Habilitar no Zabbix apenas para instâncias GCP
            try:
                hosts = zapi.host.get({
                    "output": ["hostid", "host", "description"],
                    "search": {"name": instance_name}})
                result.append(hosts)
            except Exception as e:
                print(f'Erro ao obter informações do host: {e}', flush=True)

    for listas in result:
        for hosts in listas:
            hostid = hosts['hostid']
            hostname = hosts['host']
            mensagemstatus = f"Habilitado com sucesso em {DATA}"
            print(hostname, mensagemstatus, flush=True)

if __name__ == "__main__":
    main(None, None)
