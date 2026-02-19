import logging

import requests
import yaml

from app.models import Application

logger = logging.getLogger(__name__)

def applications_from_url(applications_url: str) -> list[Application]:
    """Get the applications from the URL or the file."""

    # Note that it could be completed with applications_from_crds() as a true operator would do.
    #
    # ... but I prefer decoupling the logic from the data source.

    logger.info("get the applications from %s ...", applications_url)

    if applications_url.startswith("http") or applications_url.startswith("https"):
        apps = requests.get(applications_url).json()
    else:
        with open(applications_url, "r") as file:
            apps = yaml.safe_load(file)

    # filter out and report invalid applications
    valid_applications = []
    for app in apps:
        try:
            valid_applications.append(Application.model_validate(app))
        except ValueError as e:
            logger.warning("[%s] Invalid application: %s", app["name"], str(e))

    logger.info("found %d valid applications.", len(valid_applications))
    return valid_applications
