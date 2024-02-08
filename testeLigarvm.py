from google.auth import compute_engine
from googleapiclient import discovery
import csv
import time
from google.cloud import compute_v1

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
    # Environment setup
    project_id_gce = 'teste-lucas-non-prod'
    zone_gce = 'us-central1-a'

    # Filter GCE instances - Start
    client = compute_v1.InstancesClient()

    instances_gce = client.list(project=project_id_gce, zone=zone_gce)

    for instance in instances_gce:
        if instance.labels and instance.labels.get('auto-onoff') == 'true' and instance.status == 'TERMINATED':
            instance_name = instance.name
            start_gcp_instance(instance_name, project_id_gce, zone_gce)

        # ... (other code if needed)

if __name__ == "__main__":
    main(None, None)
