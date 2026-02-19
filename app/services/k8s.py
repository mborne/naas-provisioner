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

def namespace_exists(name: str) -> bool:
    """Check if the namespace exists."""
    try:
        api_instance.read_namespace(name)
        return True
    except client.ApiException as e:
        if e.status == 404:
            return False
        raise e

def namespace_by_name(name: str) -> client.V1Namespace:
    """Get the namespace by name."""
    return api_instance.read_namespace(name)


def namespace_find_managed() -> list[str]:
    """Get the list of the managed namespaces with the managed-by=naas-provisioner label."""

    logger.debug("get the list of the managed namespaces with the managed-by=%s label", MANAGED_BY_LABEL)

    return [namespace.metadata.name for namespace in api_instance.list_namespace(
        label_selector=f"managed-by={MANAGED_BY_LABEL}"
    ).items]


def namespace_create(app: Application) -> None:
    """Create the kubernetes namespace for the given application."""

    app_name = app.name

    if namespace_exists(app_name):
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
    namespace_update(app_name, app)


def namespace_update(app: Application) -> None:
    """Update the namespace with the application definition."""

    app_name = app.name

    if DRY_RUN:
        logger.info("[%s] skip update namespace (DRY_RUN=1)", app_name)
        return

    namespace = namespace_by_name(app_name)

    # update the namespace description
    expected_description = app.description or app.name
    if namespace.metadata.annotations is None or namespace.metadata.annotations.get("description") != expected_description:
        logger.info("[%s] update description ...", app_name)
        api_instance.patch_namespace(app_name, client.V1Namespace(
            metadata=client.V1ObjectMeta(name=app_name, labels={"managed-by": MANAGED_BY_LABEL}, annotations={"description": expected_description})
        ))
    else:
        logger.info("[%s] description is up to date", app_name)

    # update the admins RoleBindings
    rolebinding_create_or_update_admins(app)


def namespace_delete(name: str) -> None:
    """Delete the kubernetes namespace for the given name."""
    if DRY_RUN:
        logger.info("[dry-run] delete namespace %s", name)
        return

    logger.info("delete namespace %s", name)
    api_instance.delete_namespace(name, body=client.V1DeleteOptions(propagation_policy="Foreground"))

#-------------------------------------------------------------------------------------------------------
# RBAC management
#-------------------------------------------------------------------------------------------------------


def rolebinding_create_or_update_admins(app: Application) -> None:
    """Create or update the admins RoleBinding for the namespace."""
    if DRY_RUN:
        logger.info("[dry-run] create or update admins RoleBinding for namespace %s", app.name)
        return

    rolebinding_name = f"naas-provisioner-admins"
    users = []
    if app.admins is not None and app.admins.users is not None:
        users = app.admins.users

    groups = []
    if app.admins is not None and app.admins.groups is not None:
        groups = app.admins.groups

    if rolebinding_exists(app.name, rolebinding_name):
        rolebinding_update(app.name, rolebinding_name, users=users, groups=groups)
    else:
        rolebinding_create(app.name, rolebinding_name, users=users, groups=groups)


def rolebinding_exists(app_name: str, rolebinding_name: str) -> bool:
    """Check if the rolebinding exists."""
    try:
        rbac_api.read_namespaced_role_binding(rolebinding_name, app_name)
        return True
    except client.ApiException as e:
        if e.status == 404:
            return False
        raise e

def users_to_subjects(users: list[str]|None) -> list[client.RbacV1Subject]:
    """Convert the users to subjects."""
    if users is None:
        return []
    return [client.RbacV1Subject(kind="User", name=user) for user in users]

def groups_to_subjects(groups: list[str]|None) -> list[client.RbacV1Subject]:
    """Convert the groups to subjects."""
    if groups is None:
        return []
    return [client.RbacV1Subject(kind="Group", name=group) for group in groups]


def rolebinding_create(app_name: str, rolebinding_name: str, users: list[str], groups: list[str]) -> None:
    """Create a RoleBinding for the namespace."""
    if DRY_RUN:
        logger.info("[%s] skip create rolebinding %s (DRY_RUN=1)", app_name, rolebinding_name)
        return

    logger.info("[%s] create rolebinding %s ...", app_name, rolebinding_name)
    rbac_api.create_namespaced_role_binding(app_name, client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=rolebinding_name, labels={"managed-by": MANAGED_BY_LABEL}),
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))

def rolebinding_update(app_name: str, rolebinding_name: str, users: list[str], groups: list[str]) -> None:
    """Update a RoleBinding for the namespace."""

    current_subjects = rbac_api.read_namespaced_role_binding(rolebinding_name, app_name).subjects
    if current_subjects is None:
        current_subjects = []

    current_users = [subject.name for subject in current_subjects if subject.kind == "User"]
    current_groups = [subject.name for subject in current_subjects if subject.kind == "Group"]
    if current_users == users and current_groups == groups:
        logger.info("[%s] rolebinding %s is up to date", app_name, rolebinding_name)
        return

    if DRY_RUN:
        logger.info("[%s] skip update rolebinding %s (DRY_RUN=1)", app_name, rolebinding_name)
        return

    logger.info("[%s] update rolebinding %s ...", app_name, rolebinding_name )
    rbac_api.patch_namespaced_role_binding(rolebinding_name, app_name, client.V1RoleBinding(
        role_ref=client.V1RoleRef(
            api_group="rbac.authorization.k8s.io", kind="ClusterRole", name=ADMINS_CLUSTER_ROLE),
        subjects=users_to_subjects(users) + groups_to_subjects(groups),
    ))
