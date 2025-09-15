"""Canada Computers adapter - thin wrapper over generic adapter."""

from src.adapter_generic import create_snapshot
from src.models import OfferSnapshot, ProductSpec


def create_canadacomputers_snapshot(url: str, product_spec: ProductSpec) -> OfferSnapshot:
    """Create snapshot for Canada Computers - uses generic adapter."""
    return create_snapshot(url, product_spec)
