import requests
import yaml

from app.config import APPLICATIONS_URL
from app.models import Application

def get_applications() -> list[Application]:
    """Get the applications from the URL or the file."""

    # Note that it could be split into two functions:
    #
    # - get_applications_from_url()
    # - get_applications_from_crds() as a true operator would do.
    #
    # ... but I prefer decoupling the logic from the data source.

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
