"""Shared fixtures for tests."""

import pytest


@pytest.fixture
def sample_apps_yaml():
    """Minimal YAML content for a list of valid applications."""
    return """
- name: demo
  description: "Demo application"
  admins:
    groups: [oidc:devbox_admins]
    users: [oidc:user@ensg.eu]

- name: student1
  description: "Namespace for student1"
  admins:
    users: [oidc:student1@ensg.eu]
"""


@pytest.fixture
def sample_apps_dict():
    """List of dicts matching Application model (for mocking an API)."""
    return [
        {"name": "demo", "description": "Demo app", "admins": {"groups": ["oidc:admins"]}},
        {"name": "student1", "description": "Student 1", "admins": {"users": ["oidc:s1@ensg.eu"]}},
    ]
