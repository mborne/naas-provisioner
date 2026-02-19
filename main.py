from kubernetes import client, config
import time
import requests
import os
import yaml

from models import Application

APPLICATIONS_URL = os.getenv("NAAS_APPLICATIONS_URL")
if not APPLICATIONS_URL:
    raise ValueError("NAAS_APPLICATIONS_URL is not set")

config.load_kube_config()

api_instance = client.CoreV1Api()

def get_current_namespaces():
    return [namespace.metadata.name for namespace in api_instance.list_namespace().items]

def get_applications() -> list[Application]:
    """Get the applications from the URL or the file."""

    if APPLICATIONS_URL.startswith("http") or APPLICATIONS_URL.startswith("https"):
        apps = requests.get(APPLICATIONS_URL).json()
    else:
        with open(APPLICATIONS_URL, "r") as file:
            apps = yaml.safe_load(file)
    return [Application.model_validate(app) for app in apps]

def main():
    while True:
        current_namespaces = get_current_namespaces()
        print(current_namespaces)
        expected_applications = get_applications()
        for application in expected_applications:
            if application.name not in current_namespaces:
                api_instance.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=application.name)))
            else:
                #api_instance.delete_namespace(application.name)
                pass
        time.sleep(30)

if __name__ == "__main__":
    main()
