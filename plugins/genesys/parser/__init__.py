"""Genesys parser plugin registration."""

from __future__ import annotations

from parser.parser_registry import ParserRegistry

from plugins.genesys.parser.cloud import register_genesys_cloud_parsers


def register_genesys_parsers(registry: ParserRegistry) -> None:
    """Register all Genesys parsers."""
    register_genesys_cloud_parsers(registry)
