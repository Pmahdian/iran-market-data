# selenium_explorer.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

def setup_driver():
    """تنظیمات مرورگر Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # اجرای مخفی
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # غیرفعال کردن automation detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # پنهان کردن automation
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def explore_with_selenium():
    """بررسی صفحه با Selenium"""
    driver = setup_driver()
    
    try:
        print("🌐 در حال بارگذاری صفحه با Selenium...")
        url = "https://balad.ir/city-tehran/cat-supermarket"
        driver.get(url)
        
        # منتظر بارگذاری صفحه بمان
        print("⏳ منتظر بارگذاری داده‌ها...")
        time.sleep(5)  # زمان برای لود JavaScript
        
        # بررسی کنیم آیا داده‌ها لود شده‌اند
        print("\n🔍 بررسی عناصر صفحه:")
        print("-" * 40)
        
        # 1. ببینیم چه divهایی با کلاس خاص وجود دارد
        all_divs = driver.find_elements(By.TAG_NAME, "div")
        print(f"تعداد کل divها: {len(all_divs)}")
        
        # divهای با کلاس (نمونه برداری)
        div_classes = {}
        for div in all_divs[:50]:  # فقط 50 تای اول برای نمونه
            class_name = div.get_attribute("class")
            if class_name:
                div_classes[class_name] = div_classes.get(class_name, 0) + 1
        
        print("\nکلاس‌های div (نمونه):")
        for class_name, count in list(div_classes.items())[:10]:
            print(f"  '{class_name}': {count} مورد")
        
        # 2. جستجوی متن‌های مرتبط با سوپرمارکت
        print("\n🔎 جستجوی متن‌های حاوی 'سوپرمارکت':")
        page_text = driver.page_source.lower()
        if "سوپرمارکت" in page_text:
            print("✅ متن 'سوپرمارکت' در صفحه وجود دارد")
            
            # پیدا کردن المان‌های حاوی این متن
            elements_with_text = driver.find_elements(
                By.XPATH, 
                "//*[contains(text(), 'سوپرمارکت') or contains(text(), 'supermarket')]"
            )
            print(f"تعداد المان‌های حاوی 'سوپرمارکت': {len(elements_with_text)}")
            
            if elements_with_text:
                print("\nنمونه‌هایی از این المان‌ها:")
                for i, elem in enumerate(elements_with_text[:3]):
                    text = elem.text.strip()[:100]
                    print(f"  {i+1}. {text}")
                    print(f"     تگ: {elem.tag_name}, کلاس: {elem.get_attribute('class')}")
        else:
            print("❌ متن 'سوپرمارکت' در HTML اولیه نیست (شاید بعداً لود شود)")
        
        # 3. بررسی ساختار با گرفتن screenshot
        print("\n📸 گرفتن اسکرین‌شات از صفحه...")
        driver.save_screenshot("page_screenshot.png")
        print("✅ اسکرین‌شات در 'page_screenshot.png' ذخیره شد")
        
        # 4. ذخیره HTML کامل پس از اجرای JavaScript
        print("\n💾 ذخیره HTML کامل (پس از JavaScript)...")
        html_content = driver.page_source
        with open("full_page_after_js.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ HTML کامل ذخیره شد")
        
        # 5. بررسی وجود داده‌های ساختاریافته (JSON-LD)
        print("\n🔎 جستجوی داده‌های ساختاریافته (JSON-LD)...")
        script_elements = driver.find_elements(By.TAG_NAME, "script")
        json_ld_found = False
        
        for script in script_elements:
            script_type = script.get_attribute("type")
            if script_type and "json" in script_type.lower():
                content = script.get_attribute("innerHTML")
                if content and ("@type" in content or "supermarket" in content.lower()):
                    print("✅ داده‌های JSON-LD پیدا شد")
                    json_ld_found = True
                    # ذخیره نمونه
                    with open("json_ld_sample.json", "w", encoding="utf-8") as f:
                        f.write(content[:1000])
                    break
        
        if not json_ld_found:
            print("❌ داده‌های JSON-LD پیدا نشد")
        
        # 6. بررسی network requests (با لاگ کنسول)
        print("\n📡 گرفتن لاگ شبکه (console logs)...")
        logs = driver.get_log("performance")[:20]  # 20 لاگ اول
        print(f"تعداد لاگ‌های شبکه: {len(logs)}")
        
        # 7. دکمه‌های تعاملی را پیدا کن
        print("\n🔘 بررسی دکمه‌های تعاملی:")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"تعداد دکمه‌ها: {len(buttons)}")
        
        for btn in buttons[:5]:  # 5 دکمه اول
            text = btn.text.strip()
            if text:
                print(f"  دکمه: '{text[:30]}...'")
        
        # 8. آیا محتوای بیشتری با اسکرول لود می‌شود؟
        print("\n🔄 آزمایش اسکرول برای لود بیشتر...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # دوباره بررسی
        elements_after_scroll = driver.find_elements(
            By.XPATH, 
            "//*[contains(text(), 'سوپرمارکت')]"
        )
        print(f"تعداد المان‌های پس از اسکرول: {len(elements_after_scroll)}")
        
        # 9. جمع‌آوری اطلاعات اولیه
        print("\n📊 جمع‌بندی:")
        print("-" * 40)
        print("1. صفحه از Next.js استفاده می‌کند (CSR)")
        print("2. داده‌ها با JavaScript لود می‌شوند")
        print("3. نیاز به صبر برای بارگذاری کامل داریم")
        print("4. ممکن است نیاز به کلیک/اسکرول برای دیدن همه داده‌ها باشد")
        
        return driver
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None
    finally:
        # driver.quit()  # فعلاً نبندیم
        pass

def click_to_load_more(driver):
    """کلیک روی دکمه 'مشاهده بیشتر' اگر وجود دارد"""
    try:
        # دکمه‌های احتمالی
        button_selectors = [
            "//button[contains(text(), 'مشاهده بیشتر')]",
            "//button[contains(text(), 'بارگذاری بیشتر')]",
            "//button[contains(text(), 'نمایش بیشتر')]",
            "//div[contains(text(), 'مشاهده بیشتر')]",
            ".load-more",
            ".show-more"
        ]
        
        for selector in button_selectors:
            try:
                if "//" in selector:
                    button = driver.find_element(By.XPATH, selector)
                else:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                
                if button.is_displayed():
                    print(f"✅ دکمه پیدا شد: {selector}")
                    button.click()
                    time.sleep(3)
                    return True
            except:
                continue
        
        print("❌ دکمه 'مشاهده بیشتر' پیدا نشد")
        return False
        
    except Exception as e:
        print(f"⚠️ خطا در کلیک: {e}")
        return False

def extract_sample_data(driver):
    """استخراج نمونه داده از صفحه"""
    print("\n🧪 استخراج نمونه داده:")
    print("-" * 40)
    
    # راهنمای بررسی دستی
    print("برای استخراج دقیق‌تر، باید:")
    print("1. صفحه را در مرورگر باز کنید (chrome)")
    print("2. F12 بزنید (Developer Tools)")
    print("3. روی یک سوپرمارکت راست‌کلیک → Inspect")
    print("4. ساختار HTML آن را ببینید")
    print("5. سلکتور مناسب را پیدا کنید")
    
    # درخواست از کاربر برای سلکتور
    print("\n🔧 برای ادامه، نیاز داریم:")
    print("1. سلکتور CSS برای هر آیتم سوپرمارکت")
    print("2. سلکتور برای نام")
    print("3. سلکتور برای آدرس")
    print("4. سلکتور برای تلفن")
    
    # اگر سلکتورها را می‌دانی، اینجا وارد کن
    item_selector = input("\nسلکتور آیتم‌ها (مثلاً .place-card): ").strip()
    
    if item_selector:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, item_selector)
            print(f"✅ {len(items)} آیتم پیدا شد")
            
            if items:
                # بررسی اولین آیتم
                first_item = items[0]
                print(f"\n📝 محتوای اولین آیتم:")
                print(first_item.text[:500])
                
                # ذخیره HTML اولین آیتم
                with open("sample_item.html", "w", encoding="utf-8") as f:
                    f.write(first_item.get_attribute("outerHTML"))
                print("\n✅ HTML اولین آیتم در 'sample_item.html' ذخیره شد")
        
        except Exception as e:
            print(f"❌ خطا: {e}")

def main():
    print("🔬 بررسی صفحه Balad با Selenium")
    print("=" * 60)
    
    driver = explore_with_selenium()
    
    if driver:
        # آیا می‌خواهیم بیشتر بررسی کنیم؟
        choice = input("\nآیا می‌خواهید 'مشاهده بیشتر' کلیک کنیم؟ (y/n): ").strip().lower()
        if choice == 'y':
            click_to_load_more(driver)
        
        choice = input("\nآیا می‌خواهید نمونه داده استخراج کنیم؟ (y/n): ").strip().lower()
        if choice == 'y':
            extract_sample_data(driver)
        
        # باز کردن اسکرین‌شات
        print("\n📁 فایل‌های ایجاد شده:")
        print("  - page_screenshot.png (اسکرین‌شات)")
        print("  - full_page_after_js.html (HTML کامل)")
        print("  - sample_item.html (اگر استخراج کردید)")
        
        # نگه داشتن مرورگر باز برای بررسی دستی
        print("\n⚠️ مرورگر باز می‌ماند. می‌توانید دستی بررسی کنید.")
        print("برای بستن، در ترمینال Ctrl+C بزنید.")
        
        try:
            input("برای بستن Enter بزنید...")
        except KeyboardInterrupt:
            print("\nبسته شدن...")
        finally:
            driver.quit()

if __name__ == "__main__":
    main()