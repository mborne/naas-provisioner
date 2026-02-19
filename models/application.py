"""Pydantic models for applications (applications.yaml)."""

from typing import Optional

from pydantic import BaseModel, Field


class ApplicationQuotas(BaseModel):
    """Resource quotas for an application."""

    memory: str = Field(..., description="Allocated memory (e.g. 1G)")
    cpu: int | float = Field(..., description="CPU count (e.g. 1)")


class RbacEntry(BaseModel):
    """RBAC entry: role bound to groups and/or users."""

    role: str = Field(..., description="Role (e.g. admin, view)")
    groups: Optional[list[str]] = Field(default=None, description="List of groups (e.g. oidc:devbox_admins)")
    users: Optional[list[str]] = Field(default=None, description="List of users (e.g. oidc:user@ensg.eu)")


class Application(BaseModel):
    """Application definition (namespace, quotas, RBAC)."""

    name: str = Field(..., description="Application name (namespace)")
    quotas: Optional[ApplicationQuotas] = Field(default=None, description="Optional quotas")
    rbac: Optional[list[RbacEntry]] = Field(default=None, description="Optional RBAC rules")
