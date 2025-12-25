"""
Balad.ir Supermarket Scraper
Extracts all supermarkets from any Iranian city
"""

import requests
import json
import time
import sys
from typing import List, Dict, Optional

class BaladSupermarketScraper:
    # City name to URL slug mapping
    CITY_SLUGS = {
        "tehran": "tehran",
        "esfahan": "esfahan",
        "mashhad": "mashhad",
        "shiraz": "shiraz",
        "tabriz": "tabriz",
        "karaj": "karaj",
        "qom": "qom",
        "ahvaz": "ahvaz",
        "kermanshah": "kermanshah",
        "rasht": "rasht",
        "urmia": "urmia",
        "yazd": "yazd",
        "hamedan": "hamedan",
        "bandar-abbas": "bandar-abbas",
        "arak": "arak",
        "zanjan": "zanjan",
        "qazvin": "qazvin",
        "sanandaj": "sanandaj",
        "sari": "sari",
        "gorgan": "gorgan",
    }
    
    def __init__(self, city: str = "tehran", delay: float = 1.5):
        """
        Initialize scraper for a specific city
        
        Args:
            city: City name (Persian or English)
            delay: Delay between requests in seconds
        """
        self.original_city = city
        self.city_slug = self._get_city_slug(city)
        self.delay = delay
        self.base_url = f"https://balad.ir/city-{self.city_slug}/cat-supermarket"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        self.all_supermarkets = []
    
    def _get_city_slug(self, city: str) -> str:
        """Convert city name to URL slug used by Balad"""
        city_lower = city.lower()
        
        if city_lower in self.CITY_SLUGS:
            return self.CITY_SLUGS[city_lower]
        
        print(f"City '{city}' not in known cities list.")
        print("Available cities:")
        for english in list(self.CITY_SLUGS.keys())[:10]:
            print(f"  {english}")
        
        user_slug = input(f"Enter the English slug for '{city}' from Balad URL: ").strip().lower()
        return user_slug if user_slug else city_lower
    
    def fetch_page(self, page_number: int = 1) -> Optional[Dict]:
        """Fetch a single page of supermarket data"""
        try:
            url = self.base_url if page_number == 1 else f"{self.base_url}?page={page_number}"
            print(f"Fetching page {page_number}: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 404:
                print(f"Page {page_number} not found (404)")
                return None
            elif response.status_code != 200:
                print(f"HTTP error {response.status_code} for page {page_number}")
                return None
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Look for __NEXT_DATA__
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string)
                    items = self._extract_items_from_data(data)
                    
                    if items:
                        print(f"Page {page_number}: Found {len(items)} supermarkets")
                        
                        page_count = 1
                        try:
                            page_count = data['props']['pageProps']['data']['pageCount']
                            print(f"Total pages: {page_count}")
                        except:
                            pass
                        
                        return {
                            'items': items,
                            'page_number': page_number,
                            'page_count': page_count,
                            'has_next': page_number < page_count if page_count > 1 else True
                        }
                except json.JSONDecodeError as e:
                    print(f"JSON error on page {page_number}: {e}")
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Network error on page {page_number}: {e}")
            return None
    
    def _extract_items_from_data(self, data: Dict) -> List[Dict]:
        """Extract supermarket items from the data structure"""
        items = []
        
        try:
            paths_to_try = [
                ['props', 'pageProps', 'data', 'items'],
                ['items'],
                ['data', 'items'],
            ]
            
            for path in paths_to_try:
                current = data
                found = True
                
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        found = False
                        break
                
                if found and isinstance(current, list) and len(current) > 0:
                    items = current
                    break
            
            standardized_items = []
            for item in items:
                standardized = self._standardize_item(item)
                if standardized:
                    standardized_items.append(standardized)
            
            return standardized_items
            
        except Exception as e:
            print(f"Error extracting items: {e}")
            return []
    
    def _standardize_item(self, item: Dict) -> Optional[Dict]:
        """Convert raw item to standardized format"""
        try:
            name = item.get('name', '')
            if not name:
                return None
            
            telephone = item.get('telephone', '') or item.get('phone', '')
            address = item.get('address', '')
            location = {'lat': None, 'lon': None}
            
            geometry = item.get('geometry', {})
            if geometry and 'coordinates' in geometry:
                coords = geometry['coordinates']
                if len(coords) >= 2:
                    location['lon'] = coords[0]
                    location['lat'] = coords[1]
            
            if location['lat'] is None:
                geo = item.get('geo', {})
                if geo:
                    location['lat'] = geo.get('latitude')
                    location['lon'] = geo.get('longitude')
            
            return {
                'name': name.strip(),
                'phone': str(telephone).strip(),
                'address': address.strip(),
                'location': location
            }
            
        except Exception as e:
            print(f"Error standardizing item: {e}")
            return None
    
    def scrape_all_pages(self, max_pages: int = 50) -> List[Dict]:
        """Scrape all pages of supermarkets"""
        print(f"\nExtracting supermarkets from {self.original_city} ({self.city_slug})")
        print("=" * 60)
        
        page_number = 1
        total_items = 0
        page_count = None
        
        while page_number <= max_pages:
            page_data = self.fetch_page(page_number)
            
            if not page_data:
                print(f"Page {page_number} is empty or has errors.")
                break
            
            new_items = page_data.get('items', [])
            if new_items:
                self.all_supermarkets.extend(new_items)
                total_items += len(new_items)
                print(f"Total so far: {total_items} supermarkets")
            
            if 'page_count' in page_data and page_data['page_count']:
                page_count = page_data['page_count']
            
            if not page_data.get('has_next', True):
                print("Reached last page.")
                break
            
            if page_count and page_number >= page_count:
                print(f"All {page_count} pages scraped.")
                break
            
            time.sleep(self.delay)
            page_number += 1
        
        print(f"\nExtraction complete!")
        print(f"Total supermarkets in {self.original_city}: {len(self.all_supermarkets)}")
        
        return self.all_supermarkets
    
    def save_to_json(self, filename: str = None) -> str:
        """Save data to JSON file"""
        if not self.all_supermarkets:
            print("No data to save")
            return ""
        
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"supermarkets_{self.city_slug}_{timestamp}.json"
        
        try:
            filtered_data = []
            for item in self.all_supermarkets:
                filtered_item = {
                    'name': item.get('name', ''),
                    'phone': item.get('phone', ''),
                    'address': item.get('address', ''),
                    'location': item.get('location', {})
                }
                filtered_data.append(filtered_item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            print(f"Data saved to '{filename}'")
            
            import os
            file_path = os.path.abspath(filename)
            print(f"File path: {file_path}")
            
            return filename
            
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return ""


def main():
    """Main function to run the scraper"""
    print("=" * 60)
    print("Balad.ir Supermarket Scraper")
    print("=" * 60)
    
    print("\nInstructions:")
    print("- Enter city name in Persian (e.g., تهران)")
    print("- Or English name from Balad URL (e.g., esfahan)")
    print("- Supported cities: tehran, esfahan, mashhad, shiraz, tabriz, ...")
    
    default_city = "tehran"
    city_input = input(f"\nEnter city name (default: {default_city}): ").strip()
    city = city_input if city_input else default_city
    
    try:
        scraper = BaladSupermarketScraper(city=city, delay=2.0)
    except Exception as e:
        print(f"Error creating scraper: {e}")
        return
    
    try:
        supermarkets = scraper.scrape_all_pages(max_pages=30)
        
        if not supermarkets:
            print(f"\nNo supermarkets found for '{city}'.")
            return
        
        filename = scraper.save_to_json()
        
        if filename:
            print("\nSample extracted data:")
            print("-" * 50)
            
            for i, market in enumerate(supermarkets[:5], 1):
                print(f"\n{i}. {market.get('name', 'Unknown')}")
                print(f"   Phone: {market.get('phone', 'N/A')}")
                print(f"   Address: {market.get('address', 'N/A')[:80]}...")
                loc = market.get('location', {})
                if loc.get('lat') and loc.get('lon'):
                    print(f"   Location: lat={loc['lat']:.6f}, lon={loc['lon']:.6f}")
            
            print(f"\nJSON file ready: {filename}")
            print(f"Run for another city: python {sys.argv[0]} esfahan")
        
    except KeyboardInterrupt:
        print("\nOperation stopped by user.")
        if scraper.all_supermarkets:
            save = input("Save extracted data? (y/n): ").lower()
            if save == 'y':
                scraper.save_to_json()
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        city_name = sys.argv[1]
        scraper = BaladSupermarketScraper(city=city_name)
        data = scraper.scrape_all_pages(max_pages=30)
        
        if data:
            filename = f"supermarkets_{scraper.city_slug}.json"
            scraper.save_to_json(filename)
            print(f"\nExtraction of {city_name} complete. File: {filename}")
    else:
        main()