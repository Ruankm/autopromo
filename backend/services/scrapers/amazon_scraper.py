"""
Amazon Product Scraper - Extract product data from Amazon pages.

Features:
- Image extraction (high-res)
- Price data (current + original)
- Product metadata
- Rating & reviews
- Coupon detection
"""
import re
import logging
from typing import Optional, Dict
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)


class AmazonProductData:
    """Container for scraped Amazon product data."""
    def __init__(self):
        self.asin: Optional[str] = None
        self.title: Optional[str] = None
        self.image_url: Optional[str] = None
        self.current_price: Optional[float] = None
        self.original_price: Optional[float] = None
        self.discount_percent: Optional[float] = None
        self.rating: Optional[float] = None
        self.review_count: Optional[int] = None
        self.is_prime: bool = False
        self.coupon_text: Optional[str] = None
        self.availability: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "asin": self.asin,
            "title": self.title,
            "image_url": self.image_url,
            "current_price": self.current_price,
            "original_price": self.original_price,
            "discount_percent": self.discount_percent,
            "rating": self.rating,
            "review_count": self.review_count,
            "is_prime": self.is_prime,
            "coupon_text": self.coupon_text,
            "availability": self.availability
        }


class AmazonScraper:
    """Scraper for Amazon product pages."""
    
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    @staticmethod
    def extract_price(text: str) -> Optional[float]:
        """
        Extract price from text.
        
        Handles formats:
        - R$ 303,95
        - R$303.95
        - 303,95
        """
        if not text:
            return None
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[R$\s]', '', text)
        
        # Replace comma with dot
        cleaned = cleaned.replace(',', '.')
        
        # Extract first number
        match = re.search(r'(\d+\.?\d*)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    @staticmethod
    async def scrape_product(asin: str, timeout: int = 10) -> Optional[AmazonProductData]:
        """
        Scrape product data from Amazon.
        
        Args:
            asin: Amazon ASIN
            timeout: Request timeout
        
        Returns:
            AmazonProductData or None if scraping fails
        """
        url = f"https://www.amazon.com.br/dp/{asin}"
        
        headers = {
            "User-Agent": AmazonScraper.USER_AGENT,
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
            soup = BeautifulSoup(response.text, 'html.parser')
            data = AmazonProductData()
            data.asin = asin
            
            # 1. Title
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                data.title = title_elem.get_text(strip=True)
            
            # 2. Image (high-res) - Use regex to find image URLs in HTML
            # More reliable than BeautifulSoup as Amazon changes structure frequently
            image_pattern = r'https://m\.media-amazon\.com/images/I/[^"\']+\.(?:jpg|png)'
            image_matches = re.findall(image_pattern, response.text)
            
            print(f"DEBUG: Found {len(image_matches)} image matches")
            
            if image_matches:
                # Get largest available image (prefer SL1000, SL1500, or similar)
                high_res_images = [img for img in image_matches if 'SL1000' in img or 'SL1500' in img]
                if high_res_images:
                    data.image_url = high_res_images[0]
                else:
                    # Use first found image and upgrade to high-res
                    base_img = image_matches[0]
                    # Replace size parameter with SL1000 for high-res
                    data.image_url = re.sub(r'_AC_[^.]+', '_AC_SL1000_', base_img)
                
                print(f"DEBUG: Image URL = {data.image_url}")
                logger.info(f"Found image: {data.image_url[:80]}...")
            
            # 3. Current Price
            # Try multiple selectors (Amazon changes these frequently)
            price_selectors = [
                ('span', {'class': 'a-price-whole'}),
                ('span', {'class': 'a-offscreen'}),
                ('span', {'id': 'priceblock_ourprice'}),
                ('span', {'id': 'priceblock_dealprice'}),
            ]
            
            for tag, attrs in price_selectors:
                price_elem = soup.find(tag, attrs)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data.current_price = AmazonScraper.extract_price(price_text)
                    if data.current_price:
                        break
            
            # 4. Original Price (list price)
            original_selectors = [
                ('span', {'class': 'a-price a-text-price'}),
                ('span', {'class': 'priceBlockStrikePriceString'}),
                ('span', {'data-a-strike': 'true'}),
            ]
            
            for tag, attrs in original_selectors:
                original_elem = soup.find(tag, attrs)
                if original_elem:
                    original_text = original_elem.get_text(strip=True)
                    data.original_price = AmazonScraper.extract_price(original_text)
                    if data.original_price:
                        break
            
            # 5. Calculate discount
            if data.current_price and data.original_price:
                if data.original_price > data.current_price:
                    discount = ((data.original_price - data.current_price) / data.original_price) * 100
                    data.discount_percent = round(discount, 2)
            
            # 6. Rating
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                match = re.search(r'(\d+[,\.]\d+)', rating_text)
                if match:
                    try:
                        data.rating = float(match.group(1).replace(',', '.'))
                    except ValueError:
                        pass
            
            # 7. Review count
            review_elem = soup.find('span', {'id': 'acrCustomerReviewText'})
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                match = re.search(r'(\d+)', review_text.replace('.', ''))
                if match:
                    try:
                        data.review_count = int(match.group(1))
                    except ValueError:
                        pass
            
            # 8. Prime badge
            prime_elem = soup.find('i', {'class': 'a-icon-prime'})
            data.is_prime = prime_elem is not None
            
            # 9. Coupon
            coupon_elem = soup.find('span', {'class': 'promoPriceBlockMessage'})
            if coupon_elem:
                data.coupon_text = coupon_elem.get_text(strip=True)
            
            # 10. Availability
            avail_elem = soup.find('div', {'id': 'availability'})
            if avail_elem:
                data.availability = avail_elem.get_text(strip=True)
            
            logger.info(f"✅ Scraped Amazon product: {asin} - {data.title[:50] if data.title else 'N/A'}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {asin}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to scrape Amazon product {asin}: {e}")
            return None
    
    @staticmethod
    async def get_product_image(asin: str) -> Optional[str]:
        """
        Quick method to get just the product image URL.
        
        Args:
            asin: Amazon ASIN
        
        Returns:
            Image URL or None
        """
        data = await AmazonScraper.scrape_product(asin)
        return data.image_url if data else None
