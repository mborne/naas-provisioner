import argparse
import logging
import time

from app.config import LOG_LEVEL, POLL_INTERVAL_SECONDS

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
from app.services.applications import get_applications
from app.services.k8s import namespace_delete, namespace_find_managed, namespace_create, namespace_update


def synchronize():
    """Synchronize the namespaces with the applications."""
    current_namespaces = namespace_find_managed()
    expected_applications = get_applications()

    # Delete namespaces that are not in the expected applications
    expected_applications_names = [app.name for app in expected_applications]
    for ns_name in current_namespaces:
        if ns_name not in expected_applications_names:
            namespace_delete(ns_name)

    # Create or update namespaces that are in the expected applications
    for app in expected_applications:
        if app.name not in current_namespaces:
            namespace_create(app)
        else:
            namespace_update(app)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop",
        action="store_true",
        default=False,
        help="Run provisioning in a loop (default: run once and exit)",
    )
    args = parser.parse_args()

    if args.loop:
        while True:
            synchronize()
            time.sleep(POLL_INTERVAL_SECONDS)
    else:
        synchronize()


if __name__ == "__main__":
    main()
