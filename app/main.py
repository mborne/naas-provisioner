import time
import requests
import yaml

from app.config import APPLICATIONS_URL, POLL_INTERVAL_SECONDS
from app.models import Application
from app.services.kubernetes import delete_namespace, get_managed_namespaces, create_namespace, update_namespace


def get_applications() -> list[Application]:
    """Get the applications from the URL or the file."""

    if APPLICATIONS_URL.startswith("http") or APPLICATIONS_URL.startswith("https"):
        apps = requests.get(APPLICATIONS_URL).json()
    else:
        with open(APPLICATIONS_URL, "r") as file:
            apps = yaml.safe_load(file)

    # filter out and report invalid applications
    valid_applications = []
    for app in apps:
        try:
            valid_applications.append(Application.model_validate(app))
        except ValueError as e:
            print(f"Invalid application: {app['name']} - {e}")

    return valid_applications


def main():
    while True:
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
                create_namespace(app.name, app)
            else:
                update_namespace(app.name, app)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
