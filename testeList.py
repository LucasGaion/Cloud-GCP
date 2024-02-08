from google.cloud import compute_v1


def list_gce_instances(project_id, zone):
    client = compute_v1.InstancesClient()
    instances = client.list(project=project_id, zone=zone)

    for instance in instances:
        print(f'Instance Name: {instance.name}')
        print(f'Instance Status: {instance.status}')
        print('---')


if __name__ == "__main__":
    project_id_gce = 'teste-lucas-non-prod'
    zone_gce = 'us-central1-a'

    list_gce_instances(project_id_gce, zone_gce)
