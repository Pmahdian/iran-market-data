# test_balad.py
import requests
from bs4 import BeautifulSoup
import json

def test_balad():
    """یک تست ساده از سایت بلد"""
    
    # 1. به سایت بلد برو
    url = "https://balad.ir"
    
    # 2. هدرهای لازم را بگذار
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # 3. درخواست بزن
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Page Title: {BeautifulSoup(response.text, 'html.parser').title.text}")
        
        # 4. ببین آیا می‌توانیم جستجو کنیم
        # باید اول ببینیم سایت چطور کار می‌کند
        search_url = "https://balad.ir/search"
        params = {'q': 'سوپرمارکت تهران'}
        
        search_response = requests.get(search_url, headers=headers, params=params)
        print(f"\nSearch Status: {search_response.status_code}")
        
        # 5. یک نمونه کوچک ذخیره کن
        with open('test_page.html', 'w', encoding='utf-8') as f:
            f.write(search_response.text[:5000])  # فقط 5000 کاراکتر اول
        
        print("✅ تست اولیه انجام شد. فایل test_page.html ساخته شد.")
        
    except Exception as e:
        print(f"❌ خطا: {e}")

if __name__ == "__main__":
    test_balad()