"""Vendor-neutral relationship types for canonical voice topology."""

from __future__ import annotations

from enum import Enum


class RelationshipType(str, Enum):
    """Typed edges between canonical voice objects."""

    USES = "uses"
    DEPENDS_ON = "depends_on"
    CONNECTS_TO = "connects_to"
    BINDS_TO = "binds_to"
    ROUTES_TO = "routes_to"
    HOSTED_ON = "hosted_on"
    PROVIDES = "provides"
    REFERENCES = "references"
    TRANSLATES_TO = "translates_to"
    AUTHENTICATES_TO = "authenticates_to"
