import os

APPLICATIONS_URL = os.getenv("NAAS_APPLICATIONS_URL")
if not APPLICATIONS_URL:
    raise ValueError("NAAS_APPLICATIONS_URL is not set")

POLL_INTERVAL_SECONDS = int(os.getenv("NAAS_POLL_INTERVAL_SECONDS", "30"))

DRY_RUN = os.getenv("NAAS_DRY_RUN", "0").lower() == "1"

# Label used to identify namespaces managed by the provisioner.
MANAGED_BY_LABEL = "naas-provisioner"

# ClusterRole name for the admins.
ADMINS_CLUSTER_ROLE = os.getenv("NAAS_ADMINS_CLUSTER_ROLE", "admin")
