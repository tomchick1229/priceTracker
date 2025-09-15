"""Pydantic models for price tracking system."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
import hashlib


class ProductSpec(BaseModel):
    """Product specification from config."""
    id: str
    links: List[str]
    currency: Optional[str] = None
    thresholds: Optional[dict] = Field(default_factory=lambda: {"min_abs": 20, "min_pct": 0.08})


class OfferSnapshot(BaseModel):
    """Price snapshot for a specific product from a retailer."""
    product_id: str
    retailer_id: str
    url: str
    ts: str = Field(default_factory=lambda: datetime.now().isoformat())
    price: float
    currency: str
    list_price: Optional[float] = None
    in_stock: Optional[bool] = None
    parse_source: str  # "jsonld", "dom", "api"
    raw_signature: str = ""
    
    @model_validator(mode='after')
    def generate_signature(self):
        """Generate raw signature after initialization."""
        if not self.raw_signature:
            sig_data = f"{self.url}|{self.price}|{self.currency}|{self.list_price or ''}"
            self.raw_signature = hashlib.sha1(sig_data.encode()).hexdigest()
        return self


class PriceEvent(BaseModel):
    """Price drop event alert."""
    product_id: str
    retailer_id: str
    ts: str = Field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = "drop"
    old_price: float
    new_price: float
    pct_change: float
    reason: str
