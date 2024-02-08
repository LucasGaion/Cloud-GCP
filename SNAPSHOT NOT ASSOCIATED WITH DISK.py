from google.cloud import asset_v1

projetos = [
    # Adicione os nomes dos projetos GCP que deseja verificar
    'teste-lucas-non-prod',
]

nome_snapshot_schedule = "teste-lucas-backup"


def list_resources_without_snapshot_schedule(project_id):
    client = asset_v1.AssetServiceClient()
    instances_without_schedule = []
    disks_without_schedule = []

    response = client.search_all_resources(scope=f"projects/{project_id}")

    for asset in response:
        if asset.asset_type == "compute.googleapis.com/Instance" and not has_snapshot_schedule(asset.name):
            instances_without_schedule.append(asset.name)
        elif asset.asset_type == "compute.googleapis.com/Disk" and not has_snapshot_schedule(asset.name):
            disks_without_schedule.append(asset.name)

    return instances_without_schedule, disks_without_schedule


def has_snapshot_schedule(resource_name):
    client = asset_v1.AssetServiceClient()
    snapshot_filter = f'resource.name:{resource_name} AND resource.asset_type="compute.googleapis.com/Snapshot"'
    snapshots = client.search_all_resources(scope='global', query=snapshot_filter)

    return any(nome_snapshot_schedule in snapshot.asset.name for snapshot in snapshots)


if __name__ == "__main":
    for project in projetos:
        instances_without_schedule, disks_without_schedule = list_resources_without_snapshot_schedule(project)

        print(f"Projeto: {project}")
        print("Instâncias sem snapshot schedule:")
        for instance in instances_without_schedule:
            print(instance)

        print("Discos sem snapshot schedule:")
        for disk in disks_without_schedule:
            print(disk)
