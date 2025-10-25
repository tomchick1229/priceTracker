"""Config loader to read and normalize YAML product configurations."""

import yaml
from typing import List, Dict, Any
from pathlib import Path
from src.models import ProductSpec


def load_products_config(config_path: str) -> List[ProductSpec]:
    """Load and normalize product configuration from YAML file.
    
    Supports both minimal and normalized formats:
    
    Minimal (user's style):
    product:
      HF8:
        link:
          - https://link_a
          - https://link_b
    
    Normalized (preferred):
    products:
      - id: HF8
        currency: CAD
        links:
          - https://link_a
          - https://link_b
        thresholds:
          min_abs: 20
          min_pct: 0.08
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return []
    
    # Detect format and normalize
    if 'product' in data:
        # Minimal format - convert to normalized
        return _normalize_minimal_format(data['product'])
    elif 'products' in data:
        # Already normalized format
        return _parse_normalized_format(data['products'])
    else:
        raise ValueError("Config must contain either 'product' or 'products' key")


def _normalize_minimal_format(product_data: Dict[str, Any]) -> List[ProductSpec]:
    """Convert minimal format to ProductSpec list."""
    products = []
    
    for product_id, config in product_data.items():
        links = config.get('link', [])
        if isinstance(links, str):
            links = [links]
        
        # Apply default thresholds
        thresholds = config.get('thresholds', {"min_abs": 20, "min_pct": 0.08})
        
        products.append(ProductSpec(
            id=product_id,
            links=links,
            currency=config.get('currency'),
            thresholds=thresholds,
            owner=config.get('owner')
        ))
    
    return products


def _parse_normalized_format(products_data: List[Dict[str, Any]]) -> List[ProductSpec]:
    """Parse already normalized format."""
    products = []
    
    for item in products_data:
        # Apply default thresholds if missing
        if 'thresholds' not in item:
            item['thresholds'] = {"min_abs": 20, "min_pct": 0.08}
        
        products.append(ProductSpec(**item))
    
    return products
