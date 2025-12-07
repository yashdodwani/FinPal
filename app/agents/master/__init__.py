"""
Master agent package.

Exposes:
- route_request()  -> main entry point used by FastAPI /guardian route
"""

from .master_agent import route_request

__all__ = ["route_request"]
