"""
Balad.ir Supermarket Scraper - FIXED VERSION
استخراج تمام سوپرمارکت‌های یک شهر از سایت بلد
"""

import requests
import json
import time
from typing import List, Dict, Optional
import sys

class BaladSupermarketScraper:
  
    CITY_SLUGS = {
        "تهران": "tehran",
        "اصفهان": "esfahan",
        "مشهد": "mashhad",
        "شیراز": "shiraz",
        "تبریز": "tabriz",
        "کرج": "karaj",
        "قم": "qom",
        "اهواز": "ahvaz",
        "کرمانشاه": "kermanshah",
        "رشت": "rasht",
        "ارومیه": "urmia",
        "یزد": "yazd",
        "همدان": "hamedan",
        "بندرعباس": "bandar-abbas",
        "اراک": "arak",
        "زنجان": "zanjan",
        "قزوین": "qazvin",
        "سنندج": "sanandaj",
        "ساری": "sari",
        "گرگان": "gorgan",
    }
    
    def __init__(self, city: str = "تهران", delay: float = 1.5):
        """
        Initialize scraper for a specific city
        
        Args:
            city: نام شهر به فارسی یا انگلیسی (مثلاً: تهران، اصفهان، tehran, esfahan)
            delay: تأخیر بین درخواست‌ها (ثانیه)
        """
        self.original_city = city
        self.city_slug = self._get_city_slug(city)
        self.delay = delay
        self.base_url = f"https://balad.ir/city-{self.city_slug}/cat-supermarket"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        self.all_supermarkets = []
    
    def _get_city_slug(self, city: str) -> str:
      
        
        if city.lower() in self.CITY_SLUGS.values():
            return city.lower()
        
        # اگر نام فارسی شهر را وارد کرد
        if city in self.CITY_SLUGS:
            return self.CITY_SLUGS[city]
        
        # اگر شهر در دیکشنری نبود، سعی کن حدس بزنی
        print(f"⚠️  شهر '{city}' در لیست شهرهای شناخته شده نیست.")
        print("شهرهای شناخته شده:")
        for persian, english in list(self.CITY_SLUGS.items())[:10]:
            print(f"  {persian} → {english}")
        
        # از کاربر بخواه slug را وارد کند
        user_slug = input(f"\nلطفاً slug انگلیسی شهر '{city}' را در URL بلد وارد کنید: ").strip().lower()
        if user_slug:
            return user_slug
        
        # به صورت پیش‌فرض، فرض کن همان ورودی کاربر است
        print(f"⚠️  استفاده از '{city}' به عنوان slug (ممکن است کار نکند)")
        return city.lower()
    
    def fetch_page(self, page_number: int = 1) -> Optional[Dict]:
        """دریافت یک صفحه از داده‌های سوپرمارکت"""
        try:
            # ساخت URL
            if page_number == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}?page={page_number}"
            
            print(f"📄 در حال دریافت صفحه {page_number}: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            
            # بررسی وضعیت HTTP
            if response.status_code == 404:
                print(f"❌ صفحه {page_number} پیدا نشد (404)")
                return None
            elif response.status_code != 200:
                print(f"❌ خطای HTTP {response.status_code} برای صفحه {page_number}")
                return None
            
            # استخراج داده‌ها
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # روش ۱: جستجوی __NEXT_DATA__
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string)
                    items = self._extract_items_from_data(data)
                    
                    if items:
                        print(f"✅ صفحه {page_number}: {len(items)} سوپرمارکت یافت شد")
                        
                        # بررسی تعداد کل صفحات
                        page_count = 1
                        try:
                            page_count = data['props']['pageProps']['data']['pageCount']
                            print(f"📖 تعداد کل صفحات: {page_count}")
                        except:
                            pass
                        
                        return {
                            'items': items,
                            'page_number': page_number,
                            'page_count': page_count,
                            'has_next': page_number < page_count if page_count > 1 else True
                        }
                except json.JSONDecodeError as e:
                    print(f"❌ خطای JSON در صفحه {page_number}: {e}")
            
            # روش ۲: جستجوی دستی
            print(f"⚠️  صفحه {page_number}: جستجوی دستی برای داده‌ها...")
            
            # جستجوی متن سوپرمارکت در صفحه
            if "سوپرمارکت" in response.text:
                print(f"✅ صفحه {page_number} حاوی داده‌های سوپرمارکت است")
                # می‌توانیم داده‌ها را با regex استخراج کنیم
                items = self._extract_with_regex(response.text)
                if items:
                    return {
                        'items': items,
                        'page_number': page_number,
                        'has_next': True
                    }
            
            print(f"⚠️  صفحه {page_number}: هیچ داده‌ای یافت نشد")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ خطای شبکه در صفحه {page_number}: {e}")
            return None
        except Exception as e:
            print(f"❌ خطای غیرمنتظره در صفحه {page_number}: {e}")
            return None
    
    def _extract_items_from_data(self, data: Dict) -> List[Dict]:
        """استخراج آیتم‌ها از ساختار داده"""
        items = []
        
        try:
            # مسیرهای مختلف برای یافتن آیتم‌ها
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
    
    def _extract_with_regex(self, html: str) -> List[Dict]:
        """استخراج داده‌ها با استفاده از regex (روش جایگزین)"""
        items = []
        
        try:
            # الگو برای یافتن داده‌های JSON در اسکریپت‌ها
            import re
            
            # جستجوی اسکریپت‌های JSON-LD
            json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, html, re.DOTALL)
            
            for match in json_ld_matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            standardized = self._standardize_item(item)
                            if standardized:
                                items.append(standardized)
                    elif isinstance(data, dict):
                        standardized = self._standardize_item(data)
                        if standardized:
                            items.append(standardized)
                except:
                    continue
            
            return items
            
        except Exception as e:
            print(f"⚠️  خطا در استخراج با regex: {e}")
            return []
    
    def _standardize_item(self, item: Dict) -> Optional[Dict]:
        """تبدیل آیتم خام به فرمت استاندارد"""
        try:
            # استخراج نام
            name = item.get('name', '')
            if not name:
                return None
            
            # استخراج تلفن
            telephone = item.get('telephone', '') or item.get('phone', '')
            
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
                'name': name.strip(),
                'phone': str(telephone).strip(),
                'address': address.strip(),
                'location': location
            }
            
            return standardized
            
        except Exception as e:
            print(f"⚠️  خطا در استانداردسازی آیتم: {e}")
            return None
    
    def scrape_all_pages(self, max_pages: int = 50) -> List[Dict]:
        """اسکرپ تمام صفحات سوپرمارکت"""
        print(f"\n🏙️  شروع استخراج سوپرمارکت‌های {self.original_city} ({self.city_slug})")
        print("=" * 60)
        
        page_number = 1
        total_items = 0
        page_count = None
        
        while page_number <= max_pages:
            # دریافت صفحه
            page_data = self.fetch_page(page_number)
            
            if not page_data:
                print(f"\n⏹️  صفحه {page_number} خالی است یا خطا دارد.")
                break
            
            # اضافه کردن آیتم‌ها
            new_items = page_data.get('items', [])
            if new_items:
                self.all_supermarkets.extend(new_items)
                total_items += len(new_items)
                print(f"📊 تاکنون: {total_items} سوپرمارکت")
            
            # ذخیره page_count اگر موجود باشد
            if 'page_count' in page_data and page_data['page_count']:
                page_count = page_data['page_count']
            
            # بررسی ادامه‌دار بودن
            if not page_data.get('has_next', True):
                print(f"\n✅ به آخرین صفحه رسیدیم.")
                break
            
            # اگر page_count مشخص است و به آن رسیده‌ایم
            if page_count and page_number >= page_count:
                print(f"\n✅ تمام {page_count} صفحه استخراج شد.")
                break
            
            # تأخیر بین درخواست‌ها
            time.sleep(self.delay)
            
            # صفحه بعدی
            page_number += 1
        
        print(f"\n🎉 استخراج کامل شد!")
        print(f"📦 تعداد کل سوپرمارکت‌های {self.original_city}: {len(self.all_supermarkets)}")
        
        return self.all_supermarkets
    
    def save_to_json(self, filename: str = None) -> str:
        """ذخیره داده‌ها در فایل JSON"""
        if not self.all_supermarkets:
            print("⚠️  هیچ داده‌ای برای ذخیره‌سازی وجود ندارد")
            return ""
        
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_city = self.city_slug
            filename = f"supermarkets_{safe_city}_{timestamp}.json"
        
        try:
            # فقط فیلدهای مورد نظر را نگه دار
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
            
            print(f"💾 داده‌ها در فایل '{filename}' ذخیره شدند")
            
            # نمایش مسیر فایل
            import os
            file_path = os.path.abspath(filename)
            print(f"📁 مسیر فایل: {file_path}")
            
            return filename
            
        except Exception as e:
            print(f"❌ خطا در ذخیره‌سازی JSON: {e}")
            return ""


def main():
    """تابع اصلی اجرای اسکریپت"""
    print("=" * 60)
    print("🛒 Balad.ir Supermarket Scraper - FIXED")
    print("=" * 60)
    
    # اطلاعات راهنما
    print("\n📌 راهنما:")
    print("- می‌توانید نام فارسی شهر وارد کنید (مثلاً: تهران)")
    print("- یا نام انگلیسی شهر در URL بلد (مثلاً: esfahan)")
    print("- شهرهای پشتیبانی شده: تهران، اصفهان، مشهد، شیراز، تبریز، ...")
    
    # دریافت شهر از کاربر
    default_city = "تهران"
    city_input = input(f"\nنام شهر را وارد کنید (پیش‌فرض: {default_city}): ").strip()
    city = city_input if city_input else default_city
    
    # ایجاد اسکرپر
    try:
        scraper = BaladSupermarketScraper(city=city, delay=2.0)
    except Exception as e:
        print(f"❌ خطا در ایجاد اسکرپر: {e}")
        return
    
    # شروع استخراج
    try:
        supermarkets = scraper.scrape_all_pages(max_pages=30)
        
        if not supermarkets:
            print(f"\n❌ هیچ سوپرمارکتی برای شهر '{city}' یافت نشد.")
            print("علل احتمالی:")
            print("1. نام شهر را اشتباه وارد کرده‌اید")
            print("2. این شهر در بلد ثبت نشده است")
            print("3. ساختار سایت تغییر کرده است")
            print("\n💡 پیشنهاد: نام شهر را به انگلیسی امتحان کنید")
            return
        
        # ذخیره در فایل
        filename = scraper.save_to_json()
        
        if filename:
            # نمایش نمونه از داده‌ها
            print("\n📋 نمونه‌ای از داده‌های استخراج شده:")
            print("-" * 50)
            
            for i, market in enumerate(supermarkets[:5], 1):
                print(f"\n{i}. {market.get('name', 'نامشخص')}")
                print(f"   📞 تلفن: {market.get('phone', 'ندارد')}")
                print(f"   📍 آدرس: {market.get('address', 'ندارد')[:80]}...")
                loc = market.get('location', {})
                if loc.get('lat') and loc.get('lon'):
                    print(f"   🗺️  موقعیت: lat={loc['lat']:.6f}, lon={loc['lon']:.6f}")
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


# اجرای سریع از خط فرمان
if __name__ == "__main__":
    # اگر آرگومان خط فرمان داده شده باشد
    if len(sys.argv) > 1:
        city_name = sys.argv[1]
        scraper = BaladSupermarketScraper(city=city_name)
        data = scraper.scrape_all_pages(max_pages=30)
        
        if data:
            filename = f"supermarkets_{scraper.city_slug}.json"
            scraper.save_to_json(filename)
            print(f"\n✅ استخراج {city_name} کامل شد. فایل: {filename}")
        else:
            print(f"\n❌ هیچ داده‌ای برای شهر '{city_name}' یافت نشد")
    else:
        # اجرای تعاملی
        main()