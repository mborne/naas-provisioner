import json
import logging

import requests
import yaml

from app.models import Application

logger = logging.getLogger(__name__)


def _parse_json_or_yaml(content: str):
    """Parse content as JSON or YAML; try JSON first, then YAML."""
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return yaml.safe_load(content)


def applications_from_url(applications_url: str) -> list[Application]:
    """Get the applications from the URL or the file (JSON or YAML)."""

    # Note that it could be completed with applications_from_crds() as a true operator would do.
    #
    # ... but I prefer decoupling the logic from the data source.

    logger.info("get the applications from %s ...", applications_url)

    if applications_url.startswith("http") or applications_url.startswith("https"):
        response = requests.get(applications_url)
        response.raise_for_status()
        apps = _parse_json_or_yaml(response.text)
    else:
        with open(applications_url, "r", encoding="utf-8") as file:
            apps = _parse_json_or_yaml(file.read())

    if not isinstance(apps, list):
        raise ValueError(
            "Unsupported format: expected a JSON or YAML list of applications, "
            f"got {type(apps).__name__}"
        )

    # filter out and report invalid applications
    valid_applications = []
    for app in apps:
        try:
            valid_applications.append(Application.model_validate(app))
        except ValueError as e:
            logger.warning("[%s] Invalid application: %s", app["name"], str(e))

    logger.info("found %d valid applications.", len(valid_applications))
    return valid_applications
