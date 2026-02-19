"""Pydantic models for applications (applications.yaml)."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

import re

# Application name: letters and digits only, must not start with a digit, no hyphen
APPLICATION_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*$")

class RbacEntry(BaseModel):
    """RBAC entry: role bound to groups and/or users."""

    role: str = Field(..., description="Role (e.g. admin, view)")
    groups: Optional[list[str]] = Field(default=None, description="List of groups (e.g. oidc:devbox_admins)")
    users: Optional[list[str]] = Field(default=None, description="List of users (e.g. oidc:user@ensg.eu)")


class Application(BaseModel):
    """Application definition (namespace, quotas, RBAC)."""

    name: str = Field(..., description="Application name (namespace)")
    rbac: Optional[list[RbacEntry]] = Field(default=None, description="Optional RBAC rules")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not APPLICATION_NAME_PATTERN.fullmatch(v):
            raise ValueError(
                "Name must be letters and digits only, must not start with a digit, no hyphen"
            )
        return v
