from zabbix_api import ZabbixAPI

URL = 'http://172.20.211.248/zabbix/'
USUARIO = "lucas.zanatta"
SENHA = "npo@2024"

try:
    zapi = ZabbixAPI(URL, timeout=180, validate_certs=False)
    zapi.login(USUARIO, SENHA)
    print(f'Conectado na API do Zabbix: {zapi.api_version()}')
except Exception as err:
    print('Falha ao acessar a API do Zabbix')
    print('Erro: {}'.format(err))