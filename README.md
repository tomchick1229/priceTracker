# Price Tracker

A minimal proof-of-concept price tracking system that monitors product prices from URLs, stores snapshots in SQLite, and alerts when price drop thresholds are met.

## Features

- **Simple price extraction**: Uses JSON-LD structured data first, then DOM fallback
- **Multiple retailers**: Generic adapter for most sites, with Canada Computers support
- **SQLite storage**: Lightweight database for price snapshots and alerts
- **Price drop detection**: Configurable absolute and percentage thresholds
- **Amazon handling**: Stub that warns about requiring PA-API/Keepa access
- **Flexible configuration**: Supports both minimal and normalized YAML formats

## Quick Start

### 1. Install Dependencies

```bash
# Initialize project (if not already done)
uv init

# Add dependencies
uv add httpx lxml extruct w3lib pydantic pyyaml
```

### 2. Configure Products

Edit `config/products.yaml` with your products to track:

```yaml
# Minimal format
product:
  HF8:
    link:
      - https://www.canadacomputers.com/product_info.php?cPath=43_557_559&item_id=123456
      - https://www.amazon.ca/dp/B07SOMETHING
    currency: CAD
    thresholds:
      min_abs: 25      # Minimum $25 drop
      min_pct: 0.10    # Minimum 10% drop
  
  GPU1:
    link:
      - https://www.canadacomputers.com/product_info.php?cPath=43_557_558&item_id=234567
    # Uses defaults: min_abs=20, min_pct=0.08 (8%)
```

### 3. Basic Commands

```bash
# List configured products
uv run src/cli.py list

# Test a single URL
uv run src/cli.py test-url "https://www.canadacomputers.com/product_info.php?item_id=123456" --currency CAD

# Scan all products for changes
uv run src/cli.py scan

# View price history for a product
uv run src/cli.py history HF8 --limit 20
```

## Usage

### Commands

#### `list`
Display all configured products and their link counts:
```bash
uv run src/cli.py list
```

#### `test-url <url>`
Test price extraction from a single URL:
```bash
uv run src/cli.py test-url "https://www.canadacomputers.com/product_info.php?item_id=123456"
uv run src/cli.py test-url "https://www.amazon.ca/dp/B07SOMETHING" --currency CAD
```

#### `scan`
Scan all configured products for price changes:
```bash
uv run src/cli.py scan
```

#### `history <product_id>`
Show recent price history for a product:
```bash
uv run src/cli.py history HF8
uv run src/cli.py history GPU1 --limit 10
```

### Configuration Formats

The system supports two YAML configuration formats:

#### Minimal Format (User-Friendly)
```yaml
product:
  HF8:
    link:
      - https://www.canadacomputers.com/product_info.php?item_id=123456
    currency: CAD
    thresholds:
      min_abs: 20
      min_pct: 0.08
```

#### Normalized Format (Structured)
```yaml
products:
  - id: HF8
    currency: CAD
    links:
      - https://www.canadacomputers.com/product_info.php?item_id=123456
    thresholds:
      min_abs: 20
      min_pct: 0.08
```

### Supported Retailers

- **Canada Computers**: Full support via specialized adapter
- **Amazon**: Stub only (warns and skips - requires PA-API or Keepa)
- **Others**: Generic adapter using JSON-LD + DOM fallback

### Price Drop Detection

Price drops are detected when **both** thresholds are met:
- **Absolute drop**: Price decreases by at least `min_abs` dollars
- **Percentage drop**: Price decreases by at least `min_pct` percentage

Default thresholds: `min_abs=20`, `min_pct=0.08` (8%)

### Output Examples

```bash
# Successful extraction
[OK] fetched url=https://www.canadacomputers.com/... price=199.99 src=jsonld

# Price drop detected
[DROP] HF8 canadacomputers.com 199.99 last 249.99 → 199.99 (-20.0%)

# Amazon link skipped
[WARN] amazon link skipped (use PA-API/Keepa)

# Extraction failed
[ERROR] Failed to extract from https://example.com/...: Could not extract price
```

## Database Schema

The system automatically creates an SQLite database at `data/pricecheck.db` with:

### Snapshots Table
- `product_id`, `retailer_id`, `url`, `ts` (ISO timestamp)
- `price`, `currency`, `list_price`, `in_stock`
- `parse_source` ("jsonld" or "dom"), `raw_signature`

### Alerts Table  
- `product_id`, `retailer_id`, `ts`, `event_type`
- `old_price`, `new_price`, `pct_change`, `reason`

## Limitations (POC Scope)

- **No email notifications**: Prints alerts to stdout only
- **No currency conversion**: Uses detected/configured currency as-is
- **No median baselines**: Compares against last price only
- **No retries**: Single HTTP request per URL
- **Minimal error handling**: Logs errors and continues
- **No Amazon scraping**: Requires external API access

## Architecture

```
src/
├── models.py              # Pydantic data models
├── config_loader.py       # YAML configuration handling
├── storage.py             # SQLite database operations
├── extract_simple.py      # Price extraction (JSON-LD + DOM)
├── adapter_generic.py     # Generic retailer adapter
├── adapter_canadacomputers.py  # Canada Computers wrapper
├── adapter_amazon_stub.py # Amazon skip handler
├── engine.py              # Price drop detection
└── cli.py                 # Command-line interface
```

## Development

The codebase follows a modular design:
- **Models**: Pydantic for data validation and serialization
- **Storage**: SQLite with automatic schema creation
- **Extraction**: JSON-LD preferred, DOM fallback
- **Adapters**: Pluggable retailer-specific logic
- **Engine**: Centralized drop detection and deduplication
