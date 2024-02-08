import csv
import time
from googleapiclient import discovery # biblioteca que interage com varios tipos de APIs
from google.auth import compute_engine

def ligar_instancia(instance, project_id, zone):
    credentials = compute_engine.Credentials()
    service = discovery.build('compute', 'v1', credentials=credentials)
    instance_name = f'projects/{project_id}/zones/{zone}/instances/{instance}'
    try:
        #print(f'Obtendo informações da instância: {instance_name}')
        instance_data = service.instances().get(project=project_id, zone=zone, instance=instance).execute()
        #print(f'Instance Status: {instance_data["status"]}')

        if instance_data['status'] == 'TERMINATED':
            #print(f'A instância está no estado TERMINATED. Iniciando...')
            request = service.instances().start(project=project_id, zone=zone, instance=instance)
            print(f'-> Iniciando instância: {instance} no projeto: {project_id}\n')
            try:
                response = request.execute()
                #print(f'Resposta da solicitação: {response}')
                time.sleep(10)  # Adiciona um atraso maior de 10 segundos

                # Criar um novo arquivo CSV e escrever as informações do projeto, instância e status
                with open('instancias_ligadas.csv', 'a', newline='') as arquivo_saida:
                    csv_writer = csv.writer(arquivo_saida)
                    csv_writer.writerow([project_id, instance, instance_data["status"]])

            except Exception as e:
                print(f'Erro ao ligar a instância: {e}')
        else:
            print('A instância não está no estado TERMINATED. Nenhuma ação necessária.')
    except Exception as auth_error:
        print(f'Erro de autenticação: {auth_error}')


def main():
    projetos = [
        'teste-lucas-non-prod',
        'shared-project-fca',
        'non-prod-project-fca',
        'prod-project-fca',
        'sap-shared-sa',
        'sap-nonprod-sa',
        'sap-prod-sa',
        'banco-fidis-prod',
        'banco-fidis-nonprod'
    ]

    zone = 'us-central1-a'  # Substitua pela zona desejada

    with open('instancias.csv', 'r') as arquivo:
        csv_reader = csv.DictReader(arquivo)
        instancias = [linha['Nome da Instancia'] for linha in csv_reader]

    for instancia in instancias:
        instancia_encontrada = False
        for projeto in projetos:
            try:
                credentials = compute_engine.Credentials()
                service = discovery.build('compute', 'v1', credentials=credentials)
                instance_name = f'projects/{projeto}/zones/{zone}/instances/{instancia}'
                instance_data = service.instances().get(project=projeto, zone=zone, instance=instancia).execute()
                #print(f'Instância encontrada no projeto: {projeto}')
                instancia_encontrada = True
                ligar_instancia(instancia, projeto, zone)

                break
            except Exception as e:
                continue

        if not instancia_encontrada:
            print(f'Instância {instancia} não encontrada em nenhum dos projetos.')

if __name__ == "__main__":
    main()
