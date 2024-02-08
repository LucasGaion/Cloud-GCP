from zabbix_api import ZabbixAPI
from datetime import datetime
import os

def lambda_handler(event, context):
    # Variáveis de ambiente
    HOSTNAME = 'teste-lucas'  # Substitua pelo nome da instância real
    STATUS = '0'  # 0-Habilita 1-Desabilita
    URL = 'http://3.81.136.36/zabbix'
    USERNAME = "Admin"
    PASSWORD = "zabbix"
    DATA = datetime.now().strftime('%d/%m/%Y %H:%M')

    try:
        zapi = ZabbixAPI(URL, timeout=180, validate_certs=False)
        zapi.login(USERNAME, PASSWORD)
        print(f'Conectado na API do Zabbix: {zapi.api_version()}')
    except Exception as err:
        print('Falha ao acessar a API do Zabbix')
        print('Erro: {}'.format(err))

    try:
        hosts = zapi.host.get({
            "output": ["hostid", "host", "description"],
            "search": {"name": HOSTNAME}})
        for host in hosts:
            hostid = host['hostid']
            hostname = host['host']
            mensagemstatus = f"Habilitado com sucesso em {DATA}"
            zapi.host.update(
                {"hostid": hostid, "status": STATUS, "description": mensagemstatus})
            print(f"{hostname} Habilitado com sucesso em {DATA}")
    except Exception as e:
        print(f"Erro ao habilitar o status da instância: {e}")

# Invoca a função para testar a ativação do status da instância no Zabbix
lambda_handler(None, None)
