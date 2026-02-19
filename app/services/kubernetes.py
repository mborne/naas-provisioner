from kubernetes import client, config

from app.config import ADMINS_CLUSTER_ROLE, DRY_RUN, MANAGED_BY_LABEL
from app.models import Application

config.load_kube_config()

api_instance = client.CoreV1Api()
rbac_api = client.RbacAuthorizationV1Api()

def has_namespace(name: str) -> bool:
    try:
        api_instance.read_namespace(name)
        return True
    except client.ApiException as e:
        if e.status == 404:
            return False
        raise e

def get_namespace(name: str) -> client.V1Namespace:
    return api_instance.read_namespace(name)


def get_managed_namespaces() -> list[str]:
    """Get the list of the managed namespaces with the managed-by=naas-provisioner label."""
    return [namespace.metadata.name for namespace in api_instance.list_namespace(
        label_selector=f"managed-by={MANAGED_BY_LABEL}"
    ).items]


def create_namespace(name: str, app: Application) -> None:
    """Crée un namespace Kubernetes avec le nom donné."""

    if has_namespace(name):
        print(f"[warning] namespace {name} already exists, skipping creation! Please add the managed-by={MANAGED_BY_LABEL} label manually.")
        return

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

    namespace = get_namespace(name)

    # update the namespace description
    expected_description = app.description or app.name
    if namespace.metadata.annotations is None or namespace.metadata.annotations.get("description") != expected_description:
        print(f"[info] namespace {name}: update description")
        api_instance.patch_namespace(name, client.V1Namespace(
            metadata=client.V1ObjectMeta(name=name, labels={"managed-by": MANAGED_BY_LABEL}, annotations={"description": expected_description})
        ))
    else:
        print(f"[info] namespace {name}: description is already up to date")

    # update the admins RoleBindings
    create_or_update_admins_rolebinding(app)


def delete_namespace(name: str) -> None:
    """Supprime un namespace Kubernetes avec le nom donné."""
    if DRY_RUN:
        print(f"[dry-run] delete namespace {name}")
        return

    print(f"[info] delete namespace {name}")
    api_instance.delete_namespace(name, body=client.V1DeleteOptions(propagation_policy="Foreground"))

#-------------------------------------------------------------------------------------------------------
# RBAC management
#-------------------------------------------------------------------------------------------------------

def has_rolebinding(namespace: str, name: str) -> bool:
    try:
        rbac_api.read_namespaced_role_binding(name, namespace)
        return True
    except client.ApiException as e:
        if e.status == 404:
            return False
        raise e


def create_or_update_admins_rolebinding(app: Application) -> None:
    """Create or update the admins RoleBinding for the namespace."""
    if DRY_RUN:
        print(f"[dry-run] create or update admins RoleBinding for namespace {app.name}")
        return

    rolebinding_name = f"naas-provisioner-admins"

    if has_rolebinding(app.name, rolebinding_name):
        update_rolebinding(app.name, rolebinding_name, users=app.admins.users, groups=app.admins.groups)
    else:
        create_rolebinding(app.name, rolebinding_name, users=app.admins.users, groups=app.admins.groups)


def users_to_subjects(users: list[str]|None) -> list[client.RbacV1Subject]:
    if users is None:
        return []
    return [client.RbacV1Subject(kind="User", name=user) for user in users]

def groups_to_subjects(groups: list[str]|None) -> list[client.RbacV1Subject]:
    if groups is None:
        return []
    return [client.RbacV1Subject(kind="Group", name=group) for group in groups]

def create_rolebinding(app_name: str, rolebinding_name: str, users: list[str], groups: list[str]) -> None:
    """Create a RoleBinding for the namespace."""
    if DRY_RUN:
        print(f"[dry-run] create rolebinding {rolebinding_name} for namespace {app_name}")
        return

    print(f"[info] create rolebinding {rolebinding_name} for namespace {app_name}")
    rbac_api.create_namespaced_role_binding(app_name, client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=rolebinding_name, labels={"managed-by": MANAGED_BY_LABEL}),
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))

def update_rolebinding(app_name: str, rolebinding_name: str, users: list[str], groups: list[str]) -> None:
    """Update a RoleBinding for the namespace."""
    if DRY_RUN:
        print(f"[dry-run] update rolebinding {rolebinding_name} for namespace {app_name}")
        return

    current_subjects = rbac_api.read_namespaced_role_binding(rolebinding_name, app_name).subjects
    current_users = [subject.name for subject in current_subjects if subject.kind == "User"]
    current_groups = [subject.name for subject in current_subjects if subject.kind == "Group"]
    if current_users == users and current_groups == groups:
        print(f"[info] rolebinding {rolebinding_name} for namespace {app_name} is already up to date")
        return

    print(f"[info] update rolebinding {rolebinding_name} for namespace {app_name}")
    rbac_api.patch_namespaced_role_binding(rolebinding_name, app_name, client.V1RoleBinding(
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))
