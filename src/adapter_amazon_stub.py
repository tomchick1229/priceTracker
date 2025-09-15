"""Amazon stub adapter that warns and skips Amazon links."""

from src.models import ProductSpec
from src.extract_simple import SkipException


def create_amazon_snapshot(url: str, product_spec: ProductSpec):
    """Amazon stub - prints warning and raises SkipException."""
    print("[WARN] amazon link skipped (use PA-API/Keepa)")
    raise SkipException(f"Amazon requires PA-API or Keepa; skipping {url}")
