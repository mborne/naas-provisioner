"""Tests for app.services.applications (applications_from_url)."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models import Application
from app.services.applications import applications_from_url

# Test data directory
TESTS_DATA_DIR = Path(__file__).resolve().parent / "data"


class TestApplicationsFromUrl:
    """Tests for applications_from_url."""

    def test_from_file_path(self):
        """Load applications from a local YAML file."""
        path = TESTS_DATA_DIR / "sample-apps.yaml"

        result = applications_from_url(str(path))

        assert len(result) == 2
        assert all(isinstance(a, Application) for a in result)
        assert result[0].name == "demo"
        assert result[0].description == "Demo application"
        assert result[1].name == "student1"

    def test_from_http_url(self):
        """Load applications from an HTTP URL (mocked, JSON)."""
        with (TESTS_DATA_DIR / "sample-apps.json").open(encoding="utf-8") as f:
            sample_apps = json.load(f)

        with patch("app.services.applications.requests") as mock_requests:
            mock_response = mock_requests.get.return_value
            mock_response.raise_for_status = lambda: None
            mock_response.text = json.dumps(sample_apps)

            result = applications_from_url("https://example.com/apps.json")

        mock_requests.get.assert_called_once_with("https://example.com/apps.json")
        assert len(result) == 2
        assert result[0].name == "demo"
        assert result[1].name == "student1"

    def test_from_https_url(self):
        """Load applications from an HTTPS URL (mocked, JSON)."""
        with (TESTS_DATA_DIR / "sample-apps.json").open(encoding="utf-8") as f:
            sample_apps = json.load(f)

        with patch("app.services.applications.requests") as mock_requests:
            mock_response = mock_requests.get.return_value
            mock_response.raise_for_status = lambda: None
            mock_response.text = json.dumps(sample_apps)

            result = applications_from_url("https://config.example/apps.yaml")

        mock_requests.get.assert_called_once_with("https://config.example/apps.yaml")
        assert len(result) == 2

    def test_from_http_url_yaml(self):
        """Load applications from an HTTP URL returning YAML (mocked)."""
        with (TESTS_DATA_DIR / "sample-apps.yaml").open(encoding="utf-8") as f:
            yaml_content = f.read()

        with patch("app.services.applications.requests") as mock_requests:
            mock_response = mock_requests.get.return_value
            mock_response.raise_for_status = lambda: None
            mock_response.text = yaml_content

            result = applications_from_url("https://example.com/apps.yaml")

        mock_requests.get.assert_called_once_with("https://example.com/apps.yaml")
        assert len(result) == 2
        assert result[0].name == "demo"
        assert result[1].name == "student1"

    def test_from_file_path_json(self):
        """Load applications from a local JSON file."""
        path = TESTS_DATA_DIR / "sample-apps.json"
        result = applications_from_url(str(path))
        assert len(result) == 2
        assert result[0].name == "demo"
        assert result[1].name == "student1"

    def test_invalid_entries_skipped(self):
        """Invalid entries are skipped, valid ones are returned."""
        path = TESTS_DATA_DIR / "mixed.yaml"

        result = applications_from_url(str(path))

        assert len(result) == 1
        assert result[0].name == "validApp"

    def test_empty_list_returns_empty(self):
        """A file with an empty list returns an empty list."""
        path = TESTS_DATA_DIR / "empty.yaml"

        result = applications_from_url(str(path))

        assert result == []

    def test_unsupported_format_raises(self):
        """An unsupported file format (e.g. CSV) raises ValueError."""
        path = TESTS_DATA_DIR / "apps-not-supported.csv"

        with pytest.raises(ValueError, match="Unsupported format.*expected a JSON or YAML list"):
            applications_from_url(str(path))
