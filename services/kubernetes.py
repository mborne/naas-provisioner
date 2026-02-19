import os

from kubernetes import client, config

from models import Application

#DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
DRY_RUN = False
MANAGED_BY_LABEL = "naas-provisioner"

config.load_kube_config()

api_instance = client.CoreV1Api()

def get_current_namespaces() -> list[str]:
    """Get the list of the existing namespaces with the managed-by=naas-provisioner label."""
    return [namespace.metadata.name for namespace in api_instance.list_namespace(
        label_selector=f"managed-by={MANAGED_BY_LABEL}"
    ).items]


def create_namespace(name: str, app: Application) -> None:
    """Crée un namespace Kubernetes avec le nom donné."""
    if DRY_RUN:
        print(f"[dry-run] create namespace {name}")
        return

    print(f"[info] create namespace {name}")
    api_instance.create_namespace(
        client.V1Namespace(metadata=client.V1ObjectMeta(name=name, labels={"managed-by": MANAGED_BY_LABEL}))
    )
    update_namespace(name, app)


def update_namespace(name: str, app: Application) -> None:
    """Update the namespace with the application definition."""
    if DRY_RUN:
        print(f"[dry-run] update namespace {name}")
        return

    print(f"[info] update namespace {name}")
    api_instance.patch_namespace(name, client.V1Namespace(
        metadata=client.V1ObjectMeta(name=name, labels={"managed-by": MANAGED_BY_LABEL}
    )))


def delete_namespace(name: str) -> None:
    """Supprime un namespace Kubernetes avec le nom donné."""
    if DRY_RUN:
        print(f"[dry-run] delete namespace {name}")
        return

    print(f"[info] delete namespace {name}")
    api_instance.delete_namespace(name, body=client.V1DeleteOptions(propagation_policy="Foreground"))
