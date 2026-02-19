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
from app.services.kubernetes import delete_namespace, get_managed_namespaces, create_namespace, update_namespace


def synchronize():
    """Synchronize the namespaces with the applications."""
    current_namespaces = get_managed_namespaces()
    expected_applications = get_applications()

    expected_applications_names = [app.name for app in expected_applications]

    # Delete namespaces that are not in the expected applications
    for ns_name in current_namespaces:
        if ns_name not in expected_applications_names:
            delete_namespace(ns_name)

    # Create or update namespaces that are in the expected applications
    for app in expected_applications:
        if app.name not in current_namespaces:
            create_namespace(app)
        else:
            update_namespace(app.name, app)


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
