from google.auth import compute_engine
from googleapiclient import discovery
import csv
import time
from google.cloud import compute_v1
from google.cloud.exceptions import ClientError
from zabbix_api import ZabbixAPI
from datetime import datetime
import os

# Função para ligar a instância GCP
def ligar_instancia_gcp(instancia, project_id, zona):
    credenciais = compute_engine.Credentials()
    servico = discovery.build('compute', 'v1', credentials=credenciais)
    nome_instancia = f'projects/{project_id}/zones/{zona}/instances/{instancia}'
    try:
        dados_instancia = servico.instances().get(project=project_id, zone=zona, instance=instancia).execute()
        if dados_instancia['status'] == 'TERMINATED':
            requisicao = servico.instances().start(project=project_id, zone=zona, instance=instancia)
            print(f"Ligando instância: {instancia} no projeto: {project_id}, na zona: {zona}", flush=True)
            try:
                resposta = requisicao.execute()
            except Exception as e:
                print(f'Erro ao ligar a instância: {e}', flush=True)
        else:
            print('A instância não está no estado TERMINATED. Nenhuma ação necessária', flush=True)
    except Exception as erro_autenticacao:
        print(f'Erro de autenticação: {erro_autenticacao}', flush=True)

# Função principal (acesso à API do Zabbix)
def main(event, context):
    resultado = []
    URL = 'http://172.20.211.248/zabbix'
    USUARIO = "lucas.zanatta"
    SENHA = "npo@2024"
    DATA = datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        zapi = ZabbixAPI(URL, timeout=180, validate_certs=False)
        zapi.login(USUARIO, SENHA)
        print(f'Conectado à API do Zabbix: {zapi.api_version()}')
    except Exception as erro:
        print('Falha ao acessar a API do Zabbix')
        print('Erro: {}'.format(erro))

    cliente = compute_v1.InstancesClient()
    project_ids_gce = [
        'teste-lucas-non-prod',
    ]

    for project_id_gce in project_ids_gce:
        cliente = compute_v1.InstancesClient()
        zona_gce = 'us-central1-a'
        filtro_str = "labels.auto-onoff-teste-zabbix:true AND status:TERMINATED"

        try:
            instancias_gce = cliente.list(project=project_id_gce, zone=zona_gce)
            for instancia in instancias_gce:
                if instancia.labels and instancia.labels.get(
                        'auto-onoff-teste-zabbix') == 'true' and instancia.status == 'TERMINATED':
                    nome_instancia = instancia.name
                    ligar_instancia_gcp(nome_instancia, project_id_gce, zona_gce)

                    try:
                        hosts = zapi.host.get({
                            "output": ["hostid", "host", "description"],
                            "search": {"name": nome_instancia}})
                        resultado.append(hosts)
                    except Exception as e:
                        print(f'Erro ao obter informações do host: {e}', flush=True)

                    NOME_INSTANCIA = nome_instancia
                    STATUS = '0'

                    try:
                        zapi_lambda = ZabbixAPI(URL, timeout=180, validate_certs=False)
                        zapi_lambda.login(USUARIO, SENHA)
                    except Exception as erro:
                        print('Falha ao acessar a API do Zabbix (Lambda)')
                        print('Erro: {}'.format(erro))

                    try:
                        hosts_lambda = zapi_lambda.host.get({
                            "output": ["hostid", "host", "description"],
                            "search": {"name": NOME_INSTANCIA}})
                        for host in hosts_lambda:
                            hostid = host['hostid']
                            hostname = host['host']
                            mensagemstatus = f"Habilitado com sucesso em {DATA}"
                            zapi_lambda.host.update(
                                {"hostid": hostid, "status": STATUS, "description": mensagemstatus})
                            print(f"{hostname} Habilitado com sucesso em {DATA}")
                    except Exception as e:
                        print(f"Erro ao habilitar o status da instância (Lambda): {project_id_gce}:{e}")
        except Exception as e:
            print(f'Erro ao listar instâncias do projeto {project_id_gce}: {e}')

if __name__ == "__main__":
    main(None, None)

