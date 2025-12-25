# final_extractor.py
import json
import re
import requests
from bs4 import BeautifulSoup
import time

def extract_balad_supermarkets():
    """استخراج کامل سوپرمارکت‌ها از بلد"""
    
    url = "https://balad.ir/city-tehran/cat-supermarket"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://balad.ir/'
    }
    
    print("🌐 در حال دریافت داده از Balad.ir...")
    
    try:
        # 1. دریافت صفحه
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # 2. یافتن داده‌های JSON-LD
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # روش ۱: استخراج از __NEXT_DATA__ (کامل‌ترین)
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if next_data_script:
            print("✅ داده‌های __NEXT_DATA__ یافت شد")
            
            # پارس کردن JSON
            next_data = json.loads(next_data_script.string)
            
            # استخراج آیتم‌های سوپرمارکت
            items = next_data['props']['pageProps']['data']['items']
            
            print(f"📊 تعداد سوپرمارکت‌های یافت شده: {len(items)}")
            
            # تبدیل به فرمت مورد نظر ما
            supermarkets = []
            for item in items:
                supermarket = {
                    'name': item.get('name', 'نامشخص'),
                    'phone': item.get('telephone', ''),
                    'address': item.get('address', ''),
                    'location': {
                        'lat': item.get('geometry', {}).get('coordinates', [None, None])[1],
                        'lon': item.get('geometry', {}).get('coordinates', [None, None])[0]
                    },
                    'rating': item.get('rating', {}).get('score'),
                    'rating_count': item.get('rating', {}).get('count'),
                    'website': item.get('website', ''),
                    'category': item.get('category', ''),
                    'token': item.get('token', '')
                }
                supermarkets.append(supermarket)
            
            return supermarkets
        
        else:
            print("❌ داده‌های __NEXT_DATA__ یافت نشد")
            return []
            
    except Exception as e:
        print(f"❌ خطا در استخراج داده: {e}")
        return []

def extract_all_pages():
    """استخراج از تمام صفحات (صفحه‌بندی)"""
    all_supermarkets = []
    base_url = "https://balad.ir/city-tehran/cat-supermarket"
    
    # ابتدا صفحه اول را بگیریم
    print("🔍 دریافت صفحه اول...")
    page1_supermarkets = extract_balad_supermarkets()
    all_supermarkets.extend(page1_supermarkets)
    
    # بررسی صفحه‌بندی
    # معمولاً URL صفحات بعدی به این شکل است:
    # https://balad.ir/city-tehran/cat-supermarket?page=2
    
    # برای تست، فقط 3 صفحه اول را می‌گیریم
    for page in range(2, 4):  # صفحات 2 و 3
        print(f"\n🔍 دریافت صفحه {page}...")
        page_url = f"{base_url}?page={page}"
        
        try:
            # در اینجا باید منطق استخراج را برای صفحات بعدی پیاده‌سازی کنیم
            # ممکن است ساختار متفاوت باشد
            print(f"⚠️  استخراج صفحات بعدی نیاز به تنظیم بیشتر دارد")
            break  # فعلاً متوقف می‌شویم
            
        except Exception as e:
            print(f"❌ خطا در صفحه {page}: {e}")
            break
    
    return all_supermarkets

def save_to_json(data, filename):
    """ذخیره داده‌ها در فایل JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ داده‌ها در فایل '{filename}' ذخیره شد")
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره‌سازی: {e}")
        return False

def main():
    print("=" * 60)
    print("Balad.ir Supermarket Data Extractor - FINAL")
    print("=" * 60)
    
    # گزینه‌های اجرا
    print("\nانتخاب کنید:")
    print("1. استخراج فقط صفحه اول (20 آیتم)")
    print("2. استخراج چند صفحه (آزمایشی)")
    print("3. خروج")
    
    choice = input("\nگزینه شما (1/2/3): ").strip()
    
    if choice == "1":
        supermarkets = extract_balad_supermarkets()
        
        if supermarkets:
            print(f"\n✅ {len(supermarkets)} سوپرمارکت استخراج شد")
            
            # نمایش نمونه
            print("\n📋 نمونه داده‌های استخراج شده:")
            for i, market in enumerate(supermarkets[:3], 1):
                print(f"\n{i}. {market['name']}")
                print(f"   📞 تلفن: {market['phone']}")
                print(f"   📍 آدرس: {market['address'][:50]}...")
                print(f"   📍 موقعیت: lat={market['location']['lat']}, lon={market['location']['lon']}")
            
            # ذخیره در فایل
            filename = f"supermarkets_tehran_{time.strftime('%Y%m%d_%H%M%S')}.json"
            save_to_json(supermarkets, filename)
            
            # همچنین ذخیره به CSV
            save_csv = input("\nآیا می‌خواهید به CSV هم ذخیره شود؟ (y/n): ").lower()
            if save_csv == 'y':
                save_to_csv(supermarkets, filename.replace('.json', '.csv'))
    
    elif choice == "2":
        print("\n⚠️  این گزینه در حال توسعه است...")
        # supermarkets = extract_all_pages()
    
    else:
        print("\nخروج از برنامه...")

def save_to_csv(data, filename):
    """ذخیره داده‌ها در CSV"""
    try:
        import csv
        
        # نام فیلدها
        fieldnames = ['name', 'phone', 'address', 'latitude', 'longitude', 'rating', 'rating_count', 'website', 'category']
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in data:
                row = {
                    'name': item['name'],
                    'phone': item['phone'],
                    'address': item['address'],
                    'latitude': item['location']['lat'],
                    'longitude': item['location']['lon'],
                    'rating': item['rating'],
                    'rating_count': item['rating_count'],
                    'website': item['website'],
                    'category': item['category']
                }
                writer.writerow(row)
        
        print(f"✅ داده‌ها در فایل '{filename}' ذخیره شد")
        return True
        
    except ImportError:
        print("❌ کتابخانه csv موجود نیست")
        return False
    except Exception as e:
        print(f"❌ خطا در ذخیره CSV: {e}")
        return False

# تابع کمکی برای بررسی ساختار داده
def analyze_data_structure():
    """تحلیل ساختار داده‌های دریافتی"""
    url = "https://balad.ir/city-tehran/cat-supermarket"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # یافتن تمام اسکریپت‌های JSON-LD
    scripts = soup.find_all('script', {'type': 'application/ld+json'})
    
    print(f"تعداد اسکریپت‌های JSON-LD: {len(scripts)}")
    
    for i, script in enumerate(scripts):
        try:
            data = json.loads(script.string)
            print(f"\n🔹 اسکریپت {i+1}:")
            print(f"   نوع: {data.get('@type', 'ناشناخته')}")
            print(f"   نام: {data.get('name', 'ندارد')}")
            
            if 'itemListElement' in data:
                print(f"   تعداد آیتم‌ها: {len(data['itemListElement'])}")
            
        except:
            print(f"\n🔹 اسکریپت {i+1}: (خطا در پارس کردن)")

if __name__ == "__main__":
    # ابتدا ساختار داده را بررسی کنیم
    print("🔬 بررسی ساختار داده‌ها...")
    analyze_data_structure()
    
    # سپس اجرای اصلی
    main()