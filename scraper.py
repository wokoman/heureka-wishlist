"""
Heureka Wishlist Scraper.

This script logs into Heureka.cz, retrieves the user's wishlist,
and generates a static HTML page with sorting and filtering capabilities.
The data is cached daily to reduce server load.

Required environment variables:
    HEUREKA_EMAIL: Heureka account email
    HEUREKA_PASSWORD: Heureka account password

Usage:
    python scraper.py [--force-refresh]
"""

import os
import time
import json
from datetime import datetime
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def handle_cookie_consent(driver) -> bool:
    """Handles the cookie consent popup on Heureka.cz.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        bool: True if consent was handled successfully, False otherwise.
    """
    print("Attempting to handle cookie consent...")
    try:
        # Wait for and click the consent button using its specific class
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "didomi-components-button"))
        )
        print("Found consent button, attempting to click...")
        time.sleep(2)  # Small delay before clicking
        button.click()
        print("Successfully clicked consent button!")
        return True

    except Exception as e:
        print(f"Error handling cookie consent: {str(e)}")
        # Print the page source to help debug
        print("Current page source:")
        print(driver.page_source[:500])  # Print first 500 chars
        return False


def login_to_heureka() -> str:
    """Logs into Heureka account and retrieves favorites page content.

    Requires HEUREKA_EMAIL and HEUREKA_PASSWORD environment variables.

    Returns:
        str: HTML content of the favorites page.

    Raises:
        ValueError: If environment variables are not set.
        Exception: If login or page retrieval fails.
    """
    print("Initializing Safari webdriver...")
    driver = webdriver.Safari()
    driver.maximize_window()

    try:
        print("Navigating to login page...")
        driver.get("https://account.heureka.cz/auth/login")

        # Wait for page to load
        time.sleep(3)

        # Try to handle cookie consent
        if not handle_cookie_consent(driver):
            print(
                "Warning: Could not handle cookie consent, attempting to continue anyway..."
            )

        print("Waiting for login form...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )

        print("Finding password field...")
        password_field = driver.find_element(By.NAME, "password")

        print("Entering credentials...")
        email = os.getenv("HEUREKA_EMAIL")
        password = os.getenv("HEUREKA_PASSWORD")

        if not email or not password:
            raise ValueError(
                "Environment variables HEUREKA_EMAIL and HEUREKA_PASSWORD must be set"
            )

        email_field.send_keys(email)
        password_field.send_keys(password)

        print("Submitting login form...")
        password_field.submit()

        print("Waiting for login process...")
        time.sleep(5)

        print("Navigating to favorites page...")
        driver.get("https://account.heureka.cz/oblibene")

        print("Waiting for products to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-favourites-card"))
        )

        print("Getting page content...")
        content = driver.page_source
        return content

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise
    finally:
        print("Closing Safari...")
        driver.quit()


def parse_favorites(content: str) -> list:
    """Parses HTML content to extract product information.

    Args:
        content: HTML content of the favorites page.

    Returns:
        list: List of dictionaries containing product information:
            - name: Product name
            - url: Product URL
            - image_url: Product image URL
            - price: Product price (string)
    """
    soup = BeautifulSoup(content, "html.parser")
    products = []

    # Find all product cards
    for card in soup.find_all("article", class_="c-favourites-card"):
        product = {}

        # Get product link and name
        link_elem = card.find("a")
        if link_elem:
            product["url"] = link_elem.get("href")
            product["name"] = link_elem.get("title", "").strip()

        # Get product image
        img_elem = card.find("img", class_="c-favourites-card__image")
        if img_elem:
            product["image_url"] = img_elem.get("src")

        # Get product price
        price_elem = card.find("strong", class_="c-favourites-card__price")
        if price_elem:
            # Clean up the price text (remove "od" and "Kč")
            price_text = price_elem.text.strip()
            price_text = price_text.replace("od", "").replace("Kč", "").strip()
            product["price"] = price_text
        else:
            product["price"] = "Cena není k dispozici"

        # Add the product if we found at least a name
        if product.get("name"):
            products.append(product)

    return products


def generate_html(products: list) -> None:
    """Generates HTML page from product data.

    Args:
        products: List of product dictionaries.

    Creates wishlist.html file in the current directory.
    """
    # Define CSS separately for better readability
    css = """
    body {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: #fafafa;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #444;
    }
    
    .controls {
        background: white;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        border: 1px solid #e0e0e0;
    }
    
    .filter-section {
        margin-top: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }
    
    .price-inputs {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .price-filter input {
        width: 100px;
        height: 36px;  /* Match button height */
        padding: 8px 12px;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        font-size: 14px;
        color: #444;
        background: white;
    }
    
    .price-label {
        color: #666;
        font-size: 14px;
        margin-right: 4px;
    }
    
    .price-separator {
        color: #666;
        margin: 0 4px;
    }
    
    .sort-controls {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 10px;
        margin-bottom: 20px;
    }
    
    button {
        background-color: white;
        color: #666;
        border: 1px solid #e0e0e0;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        font-weight: normal;
        transition: all 0.2s ease;
    }
    
    button:hover {
        background-color: #f5f5f5;
        border-color: #ccc;
    }
    
    .product-card {
        background: white;
        padding: 25px;
        margin-bottom: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        display: flex;
        align-items: center;
        gap: 25px;
        transition: all 0.2s ease;
    }
    
    .product-card:hover {
        border-color: #ccc;
    }
    
    .product-image {
        width: 120px;
        height: 120px;
        object-fit: contain;
    }
    
    .product-info {
        flex-grow: 1;
    }
    
    .product-info h3 {
        margin: 0 0 12px 0;
        color: #444;
        font-weight: normal;
        font-size: 18px;
    }
    
    .product-info a {
        color: #444;
        text-decoration: none;
    }
    
    .product-info a:hover {
        color: #000;
    }
    
    .product-price {
        color: #666;
        margin: 8px 0;
        font-size: 16px;
    }
    
    .product-date {
        color: #888;
        font-size: 13px;
    }
    
    .hidden {
        display: none !important;
    }
    
    h1 {
        color: #444;
        font-weight: normal;
        margin-bottom: 30px;
        font-size: 24px;
    }
    """

    # Updated HTML with new controls
    html_content = f"""
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Heureka Wishlist</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <style>
    {css}
    </style>
</head>
<body>
    <h1>My Heureka Wishlist</h1>
    
    <div class="controls">
        <div class="sort-controls">
            <button onclick="sortByDate('desc')">Nejnovější první</button>
            <button onclick="sortByDate('asc')">Nejstarší první</button>
            <button onclick="sortByPrice('asc')">Nejlevnější první</button>
            <button onclick="sortByPrice('desc')">Nejdražší první</button>
        </div>
        
        <div class="filter-section">
            <div class="price-inputs">
                <label class="price-label">
                    <input type="number" id="minPrice" placeholder="Min Kč" onchange="applyPriceFilter()">
                </label>
                <label class="price-separator">-</label>
                <label class="price-label">
                    <input type="number" id="maxPrice" placeholder="Max Kč" onchange="applyPriceFilter()">
                </label>
            </div>
            <button onclick="resetFilters()">Reset filtrů</button>
        </div>
    </div>

    <div id="products-container">
"""

    # Add each product with price data attribute
    for index, product in enumerate(products):
        # Convert price to number for sorting (remove spaces and non-numeric chars)
        price_value = (
            "".join(filter(str.isdigit, product["price"])) if product["price"] else "0"
        )

        html_content += f"""
        <article class="product-card" data-index="{index}" data-price="{price_value}">
            <img class="product-image" src="{product['image_url']}" alt="{product['name']}">
            <div class="product-info">
                <h3><a href="{product['url']}" target="_blank">{product['name']}</a></h3>
                <div class="product-price">od {product['price']} Kč</div>
                <div class="product-date">Pořadí v seznamu: {index + 1}</div>
            </div>
        </article>
"""

    # Add the closing tags and JavaScript with sorting and filtering functions
    html_content += """
    </div>

    <script>
        function sortByDate(direction) {
            const container = document.getElementById('products-container');
            const productElements = Array.from(container.children);
            
            productElements.sort((a, b) => {
                const indexA = parseInt(a.dataset.index);
                const indexB = parseInt(b.dataset.index);
                return direction === 'asc' ? indexB - indexA : indexA - indexB;
            });
            
            container.innerHTML = '';
            productElements.forEach(elem => container.appendChild(elem));
        }

        function sortByPrice(direction) {
            const container = document.getElementById('products-container');
            const productElements = Array.from(container.children);
            
            productElements.sort((a, b) => {
                const priceA = parseInt(a.dataset.price) || 0;
                const priceB = parseInt(b.dataset.price) || 0;
                return direction === 'asc' ? priceA - priceB : priceB - priceA;
            });
            
            container.innerHTML = '';
            productElements.forEach(elem => container.appendChild(elem));
        }

        function applyPriceFilter() {
            const minPrice = parseInt(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseInt(document.getElementById('maxPrice').value) || Infinity;
            
            const products = document.querySelectorAll('.product-card');
            products.forEach(product => {
                const price = parseInt(product.dataset.price) || 0;
                if (price >= minPrice && price <= maxPrice) {
                    product.classList.remove('hidden');
                } else {
                    product.classList.add('hidden');
                }
            });
        }

        function resetFilters() {
            document.getElementById('minPrice').value = '';
            document.getElementById('maxPrice').value = '';
            document.querySelectorAll('.product-card').forEach(product => {
                product.classList.remove('hidden');
            });
        }
    </script>
</body>
</html>
"""

    # Save the HTML file
    with open("wishlist.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def load_cached_data() -> list:
    """Loads cached product data if available and recent.

    Returns:
        list: List of product dictionaries if cache is valid,
             None otherwise.
    """
    try:
        if os.path.exists("wishlist_data.json"):
            with open("wishlist_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Check if data is from today
                last_updated = datetime.fromisoformat(data["last_updated"])
                if last_updated.date() == datetime.now().date():
                    print("Using cached data from today")
                    return data["products"]
                print("Cache is old, fetching fresh data")
                return None
    except Exception as e:
        print(f"Error loading cached data: {e}")
        return None
    return None


def save_to_json(products: list) -> None:
    """Saves product data to JSON cache file.

    Args:
        products: List of product dictionaries.

    Creates wishlist_data.json file in the current directory.
    """
    data = {"last_updated": datetime.now().isoformat(), "products": products}
    with open("wishlist_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Saved products to wishlist_data.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Heureka wishlist")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force refresh data from Heureka instead of using cache",
    )
    args = parser.parse_args()

    try:
        # Try to load cached data first (unless force refresh is requested)
        products = None if args.force_refresh else load_cached_data()

        # If no cached data or force refresh, scrape the website
        if products is None:
            content = login_to_heureka()
            print("Successfully logged in!")

            # Parse the products
            products = parse_favorites(content)
            print(f"\nFound {len(products)} products")

            # Save to JSON for future use
            save_to_json(products)

        # Generate the HTML regardless of data source
        generate_html(products)
        print("Generated wishlist.html file")

    except Exception as e:
        print(f"\nError: {str(e)}")
