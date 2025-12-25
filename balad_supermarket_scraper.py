#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Balad.ir Supermarket Scraper
استخراج تمام سوپرمارکت‌های یک شهر از سایت بلد
"""

import requests
import json
import time
from typing import List, Dict, Optional
import sys
import os

class BaladSupermarketScraper:
    def __init__(self, city: str = "تهران", delay: float = 1.0):
        """
        Initialize scraper for a specific city
        
        Args:
            city: نام شهر به فارسی (مثلاً: تهران، اصفهان، مشهد)
            delay: تأخیر بین درخواست‌ها (ثانیه)
        """
        self.city = city
        self.delay = delay
        self.base_url = f"https://balad.ir/city-{city}/cat-supermarket"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.all_supermarkets = []
    
    def fetch_page(self, page_number: int = 1) -> Optional[Dict]:
        """
        Fetch a single page of supermarket data
        
        Args:
            page_number: شماره صفحه
            
        Returns:
            دیکشنری حاوی داده‌های صفحه یا None در صورت خطا
        """
        try:
            url = f"{self.base_url}?page={page_number}" if page_number > 1 else self.base_url
            
            print(f"📄 در حال دریافت صفحه {page_number}...")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # استخراج داده‌های JSON از HTML
            import re
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # روش ۱: جستجوی داده‌ها در __NEXT_DATA__
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if next_data_script:
                data = json.loads(next_data_script.string)
                
                # استخراج آیتم‌ها از ساختار داده
                items = self._extract_items_from_data(data)
                
                if items:
                    print(f"✅ صفحه {page_number}: {len(items)} سوپرمارکت یافت شد")
                    return {
                        'items': items,
                        'page_number': page_number,
                        'has_next': self._has_next_page(data, page_number)
                    }
            
            # روش ۲: جستجوی مستقیم در JSON-LD
            json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list) and len(data) > 0 and 'name' in data[0]:
                        items = self._extract_from_json_ld(data)
                        if items:
                            print(f"✅ صفحه {page_number}: {len(items)} سوپرمارکت یافت شد")
                            return {
                                'items': items,
                                'page_number': page_number,
                                'has_next': True  # فرض می‌کنیم صفحه بعدی وجود دارد
                            }
                except:
                    continue
            
            print(f"⚠️  صفحه {page_number}: هیچ داده‌ای یافت نشد")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطا در دریافت صفحه {page_number}: {e}")
            return None
        except Exception as e:
            print(f"❌ خطای غیرمنتظره در صفحه {page_number}: {e}")
            return None
    
    def _extract_items_from_data(self, data: Dict) -> List[Dict]:
        """
        Extract supermarket items from the data structure
        """
        items = []
        
        try:
            # مسیرهای مختلف برای یافتن آیتم‌ها
            paths_to_try = [
                # مسیر اصلی در Balad
                ['props', 'pageProps', 'data', 'items'],
                # مسیرهای جایگزین
                ['items'],
                ['data', 'items'],
                ['result', 'items']
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
                
                if found and isinstance(current, list):
                    items = current
                    break
            
            # تبدیل به فرمت استاندارد
            standardized_items = []
            for item in items:
                standardized = self._standardize_item(item)
                if standardized:
                    standardized_items.append(standardized)
            
            return standardized_items
            
        except Exception as e:
            print(f"⚠️  خطا در استخراج آیتم‌ها: {e}")
            return []
    
    def _extract_from_json_ld(self, data: List[Dict]) -> List[Dict]:
        """
        Extract from JSON-LD structured data
        """
        items = []
        
        for item in data:
            try:
                standardized = {
                    'name': item.get('name', ''),
                    'telephone': item.get('telephone', ''),
                    'address': item.get('address', ''),
                    'location': item.get('geo', {})
                }
                
                # فقط اگر نام داشته باشد اضافه کن
                if standardized['name']:
                    items.append(standardized)
            except:
                continue
        
        return items
    
    def _standardize_item(self, item: Dict) -> Optional[Dict]:
        """
        Convert raw item to standardized format
        """
        try:
            # استخراج نام
            name = item.get('name', '')
            if not name:
                return None
            
            # استخراج تلفن
            telephone = item.get('telephone', '')
            
            # استخراج آدرس
            address = item.get('address', '')
            
            # استخراج موقعیت مکانی
            location = {'lat': None, 'lon': None}
            
            # بررسی geometry برای مختصات
            geometry = item.get('geometry', {})
            if geometry and 'coordinates' in geometry:
                coords = geometry['coordinates']
                if len(coords) >= 2:
                    # فرمت: [longitude, latitude]
                    location['lon'] = coords[0]
                    location['lat'] = coords[1]
            
            # اگر geometry نبود، geo را بررسی کن
            if location['lat'] is None:
                geo = item.get('geo', {})
                if geo:
                    location['lat'] = geo.get('latitude')
                    location['lon'] = geo.get('longitude')
            
            # ساخت آیتم استاندارد
            standardized = {
                'name': name,
                'phone': telephone,
                'address': address,
                'location': location
            }
            
            # حذف فیلدهای خالی
            return {k: v for k, v in standardized.items() if v not in [None, '', {}]}
            
        except Exception as e:
            print(f"⚠️  خطا در استانداردسازی آیتم: {e}")
            return None
    
    def _has_next_page(self, data: Dict, current_page: int) -> bool:
        """
        Check if there are more pages
        """
        try:
            # بررسی pageCount
            page_count = data.get('props', {}).get('pageProps', {}).get('data', {}).get('pageCount', 0)
            if page_count > current_page:
                return True
            
            # بررسی وجود آیتم‌ها
            items = self._extract_items_from_data(data)
            if items and len(items) > 0:
                return True
            
            return False
            
        except:
            # به صورت پیش‌فرض فرض کن صفحه بعدی وجود دارد
            return True
    
    def scrape_all_pages(self, max_pages: int = 100) -> List[Dict]:
        """
        Scrape all pages of supermarkets
        
        Args:
            max_pages: حداکثر تعداد صفحات برای اسکرپ
            
        Returns:
            لیست تمام سوپرمارکت‌ها
        """
        print(f"\n🏙️  شروع استخراج سوپرمارکت‌های {self.city}")
        print("=" * 50)
        
        page_number = 1
        total_items = 0
        
        while page_number <= max_pages:
            # دریافت صفحه
            page_data = self.fetch_page(page_number)
            
            if not page_data or not page_data['items']:
                print(f"\n⏹️  صفحه {page_number} خالی است. توقف اسکرپ.")
                break
            
            # اضافه کردن آیتم‌ها
            new_items = page_data['items']
            self.all_supermarkets.extend(new_items)
            total_items += len(new_items)
            
            print(f"📊 تاکنون: {total_items} سوپرمارکت جمع‌آوری شده")
            
            # بررسی ادامه‌دار بودن
            if not page_data.get('has_next', True):
                print(f"\n✅ به آخرین صفحه رسیدیم.")
                break
            
            # تأخیر بین درخواست‌ها
            time.sleep(self.delay)
            
            # صفحه بعدی
            page_number += 1
        
        print(f"\n🎉 استخراج کامل شد!")
        print(f"📦 تعداد کل سوپرمارکت‌های {self.city}: {len(self.all_supermarkets)}")
        
        return self.all_supermarkets
    
    def remove_duplicates(self) -> List[Dict]:
        """
        Remove duplicate supermarkets based on name and address
        """
        unique_supermarkets = []
        seen = set()
        
        for supermarket in self.all_supermarkets:
            # ایجاد کلید یکتا از نام و آدرس
            key = f"{supermarket.get('name', '')}|{supermarket.get('address', '')}"
            
            if key not in seen:
                seen.add(key)
                unique_supermarkets.append(supermarket)
        
        removed = len(self.all_supermarkets) - len(unique_supermarkets)
        if removed > 0:
            print(f"♻️  {removed} تکراری حذف شدند")
        
        self.all_supermarkets = unique_supermarkets
        return unique_supermarkets
    
    def save_to_json(self, filename: str = None) -> str:
        """
        Save data to JSON file
        
        Args:
            filename: نام فایل خروجی
            
        Returns:
            مسیر فایل ذخیره شده
        """
        if not self.all_supermarkets:
            print("⚠️  هیچ داده‌ای برای ذخیره‌سازی وجود ندارد")
            return ""
        
        if not filename:
            # ساخت نام فایل خودکار
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_city = self.city.replace(" ", "_")
            filename = f"supermarkets_{safe_city}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_supermarkets, f, ensure_ascii=False, indent=2)
            
            print(f"💾 داده‌ها در فایل '{filename}' ذخیره شدند")
            return filename
            
        except Exception as e:
            print(f"❌ خطا در ذخیره‌سازی JSON: {e}")
            return ""
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about collected data
        """
        stats = {
            'total': len(self.all_supermarkets),
            'with_phone': 0,
            'with_location': 0,
            'with_address': 0
        }
        
        for supermarket in self.all_supermarkets:
            if supermarket.get('phone'):
                stats['with_phone'] += 1
            
            location = supermarket.get('location', {})
            if location.get('lat') and location.get('lon'):
                stats['with_location'] += 1
            
            if supermarket.get('address'):
                stats['with_address'] += 1
        
        return stats


# تابع اصلی برای اجرای اسکریپت
def main():
    """تابع اصلی اجرای اسکریپت"""
    
    print("=" * 60)
    print("🛒 Balad.ir Supermarket Scraper")
    print("=" * 60)
    
    # دریافت شهر از کاربر
    default_city = "تهران"
    city_input = input(f"نام شهر را وارد کنید (پیش‌فرض: {default_city}): ").strip()
    city = city_input if city_input else default_city
    
    # ایجاد اسکرپر
    scraper = BaladSupermarketScraper(city=city, delay=1.5)
    
    # شروع استخراج
    try:
        supermarkets = scraper.scrape_all_pages(max_pages=50)  # حداکثر 50 صفحه
        
        if not supermarkets:
            print("\n❌ هیچ سوپرمارکتی یافت نشد.")
            print("علل احتمالی:")
            print("1. نام شهر را اشتباه وارد کرده‌اید")
            print("2. در این شهر سوپرمارکتی ثبت نشده است")
            print("3. ساختار سایت تغییر کرده است")
            return
        
        # حذف تکراری‌ها
        unique_supermarkets = scraper.remove_duplicates()
        
        # آمار
        stats = scraper.get_statistics()
        print("\n📊 آمار نهایی:")
        print(f"   تعداد کل: {stats['total']}")
        print(f"   دارای تلفن: {stats['with_phone']}")
        print(f"   دارای موقعیت مکانی: {stats['with_location']}")
        print(f"   دارای آدرس: {stats['with_address']}")
        
        # ذخیره در فایل
        filename = scraper.save_to_json()
        
        if filename:
            # نمایش نمونه از داده‌ها
            print("\n📋 نمونه‌ای از داده‌های استخراج شده:")
            print("-" * 50)
            
            for i, market in enumerate(unique_supermarkets[:3], 1):
                print(f"\n{i}. {market.get('name', 'نامشخص')}")
                print(f"   📞 تلفن: {market.get('phone', 'ندارد')}")
                print(f"   📍 آدرس: {market.get('address', 'ندارد')[:60]}...")
                loc = market.get('location', {})
                if loc.get('lat') and loc.get('lon'):
                    print(f"   🗺️  موقعیت: ({loc['lat']:.6f}, {loc['lon']:.6f})")
                else:
                    print(f"   🗺️  موقعیت: ندارد")
            
            print(f"\n✅ فایل JSON شما آماده است: {filename}")
            print(f"🔧 برای شهر دیگر اجرا کنید: python {sys.argv[0]} اصفهان")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  عملیات توسط کاربر متوقف شد.")
        if scraper.all_supermarkets:
            save = input("آیا داده‌های استخراج شده ذخیره شوند؟ (y/n): ").lower()
            if save == 'y':
                scraper.save_to_json()
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")


# تابع برای استفاده آسان از خط فرمان
def quick_scrape(city: str, output_file: str = None):
    """
    اسکرپ سریع یک شهر
    
    مثال استفاده:
    >>> from balad_supermarket_scraper import quick_scrape
    >>> data = quick_scrape("اصفهان", "supermarkets_isfahan.json")
    """
    scraper = BaladSupermarketScraper(city=city)
    data = scraper.scrape_all_pages(max_pages=30)
    data = scraper.remove_duplicates()
    
    if output_file:
        scraper.save_to_json(output_file)
    
    return data


if __name__ == "__main__":
    # اگر آرگومان خط فرمان داده شده باشد
    if len(sys.argv) > 1:
        city_name = sys.argv[1]
        scraper = BaladSupermarketScraper(city=city_name)
        data = scraper.scrape_all_pages()
        scraper.remove_duplicates()
        
        filename = f"supermarkets_{city_name}.json"
        scraper.save_to_json(filename)
        
        print(f"\n✅ استخراج {city_name} کامل شد. فایل: {filename}")
    else:
        # اجرای تعاملی
        main()