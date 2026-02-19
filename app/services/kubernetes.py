import logging

from kubernetes import client, config

from app.config import ADMINS_CLUSTER_ROLE, DRY_RUN, MANAGED_BY_LABEL
from app.models import Application

logger = logging.getLogger(__name__)


def _load_kubernetes_config() -> None:
    """Load Kubernetes config: in-cluster when running inside a pod, otherwise local kubeconfig."""
    try:
        config.load_incluster_config()
        logger.info("Kubernetes config loaded (in-cluster)")
    except config.ConfigException:
        config.load_kube_config()
        logger.debug("Kubernetes config loaded (local kubeconfig)")


_load_kubernetes_config()

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

    logger.debug("get the list of the managed namespaces with the managed-by=%s label", MANAGED_BY_LABEL)

    return [namespace.metadata.name for namespace in api_instance.list_namespace(
        label_selector=f"managed-by={MANAGED_BY_LABEL}"
    ).items]


def create_namespace(app: Application) -> None:
    """Create the kubernetes namespace for the given application."""

    app_name = app.name

    if has_namespace(app_name):
        logger.warning(
            "[%s] namespace already exists without the managed-by=%s label manually. Please add it manually.",
            app_name,
            MANAGED_BY_LABEL
        )
        return

    if DRY_RUN:
        logger.info("[%s] create namespace (skipped, DRY_RUN=1)", app_name)
        return

    logger.info("[%s] create namespace ...", app_name)
    api_instance.create_namespace(
        client.V1Namespace(metadata=client.V1ObjectMeta(name=app_name, labels={"managed-by": MANAGED_BY_LABEL}))
    )
    update_namespace(app_name, app)


def update_namespace(name: str, app: Application) -> None:
    """Update the namespace with the application definition."""
    if DRY_RUN:
        logger.info("[%s] skip update namespace (DRY_RUN=1)", name)
        return

    namespace = get_namespace(name)

    # update the namespace description
    expected_description = app.description or app.name
    if namespace.metadata.annotations is None or namespace.metadata.annotations.get("description") != expected_description:
        logger.info("[%s] update description ...", name)
        api_instance.patch_namespace(name, client.V1Namespace(
            metadata=client.V1ObjectMeta(name=name, labels={"managed-by": MANAGED_BY_LABEL}, annotations={"description": expected_description})
        ))
    else:
        logger.info("[%s] description is already up to date", name)

    # update the admins RoleBindings
    create_or_update_admins_rolebinding(app)


def delete_namespace(name: str) -> None:
    """Delete the kubernetes namespace for the given name."""
    if DRY_RUN:
        logger.info("[dry-run] delete namespace %s", name)
        return

    logger.info("delete namespace %s", name)
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
        logger.info("[dry-run] create or update admins RoleBinding for namespace %s", app.name)
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
        logger.info("[dry-run] create rolebinding %s for namespace %s", rolebinding_name, app_name)
        return

    logger.info("[%s] create rolebinding %s ...", app_name, rolebinding_name)
    rbac_api.create_namespaced_role_binding(app_name, client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=rolebinding_name, labels={"managed-by": MANAGED_BY_LABEL}),
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))

def update_rolebinding(app_name: str, rolebinding_name: str, users: list[str], groups: list[str]) -> None:
    """Update a RoleBinding for the namespace."""
    if DRY_RUN:
        logger.info("[dry-run] update rolebinding %s for namespace %s", rolebinding_name, app_name)
        return

    current_subjects = rbac_api.read_namespaced_role_binding(rolebinding_name, app_name).subjects
    current_users = [subject.name for subject in current_subjects if subject.kind == "User"]
    current_groups = [subject.name for subject in current_subjects if subject.kind == "Group"]
    if current_users == users and current_groups == groups:
        logger.info("[%s] rolebinding %s is already up to date", app_name, rolebinding_name)
        return

    logger.info("[%s] update rolebinding %s ...", app_name, rolebinding_name )
    rbac_api.patch_namespaced_role_binding(rolebinding_name, app_name, client.V1RoleBinding(
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))
