# Heureka Wishlist Scraper

A Python script that scrapes your Heureka.cz wishlist and creates a sortable HTML page of your favorite products.

## Features

- Scrapes products from your Heureka wishlist
- Creates a responsive HTML page with sorting and filtering
- Caches data to reduce server load
- Handles cookie consent automatically
- Supports price-based sorting and filtering
- Mobile-friendly design

## Prerequisites

- Python 3.6+
- One of the following browsers and drivers:
  - Firefox (recommended) with geckodriver
  - Safari with SafariDriver
- Environment variables for Heureka login

## Installation

1. Clone this repository
2. Install required packages:

   ```bash
   pip install selenium beautifulsoup4
   ```

3. Install browser driver:
   - For Firefox (recommended):

     ```bash
     # On macOS with Homebrew:
     brew install geckodriver

     # On Ubuntu/Debian:
     sudo apt install firefox-geckodriver
     ```

   - For Safari:
     Enable WebDriver in Safari's Developer menu

## Configuration

Set your Heureka credentials as environment variables:

```bash
export HEUREKA_EMAIL="your-email@example.com"
export HEUREKA_PASSWORD="your-password"
```

## Usage

Basic usage (uses Firefox in headless mode):

```bash
python scraper.py
```

Use Safari instead:

```bash
python scraper.py --browser safari
```

Run with visible browser window:

```bash
python scraper.py --no-headless
```

Force refresh and specify browser:

```bash
python scraper.py --force-refresh --browser firefox
```

## Output Files

The script generates two files:

- `wishlist.html`: A formatted webpage of your wishlist
- `wishlist_data.json`: Cached product data

## Generated Page Features

The HTML page includes:

- Product sorting:
  - Newest/Oldest first
  - Price (low to high/high to low)
- Price range filtering
- Responsive design
- Clean, minimal interface

## Technical Details

- Uses Safari WebDriver for web automation
- BeautifulSoup4 for HTML parsing
- Daily caching of product data
- Responsive CSS design
- JavaScript for client-side sorting and filtering

## Error Handling

- Automatic cookie consent handling
- Graceful failure for missing credentials
- Cache validation and fallback
- Debug output for common issues

## Notes

- Data is cached daily to reduce load on Heureka's servers
- Uses Safari WebDriver (modify for other browsers if needed)
- Requires valid Heureka account credentials
- All prices are in CZK (Czech Koruna)

## License

This project is licensed under the Mozilla Public License 2.0 - see the [LICENSE](LICENSE) file for details.
