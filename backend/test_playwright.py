from playwright.sync_api import sync_playwright
import time

def test_diyetkolik():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False ile görebiliriz
        page = browser.new_page()
        
        url = "https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik"
        print(f"Sayfa yükleniyor: {url}")
        
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Daha fazla bekle
        print("JavaScript'in render olması için bekleniyor...")
        time.sleep(5)
        
        # Sayfanın screenshot'ını al
        page.screenshot(path="diyetkolik_screenshot.png")
        print("Screenshot kaydedildi: diyetkolik_screenshot.png")
        
        # Sayfanın HTML'ini kaydet
        content = page.content()
        with open("diyetkolik_page.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML kaydedildi: diyetkolik_page.html")
        
        # Olası seçicileri test et
        selectors = [
            "table",
            "table tbody tr",
            "div[class*='food']",
            "div[class*='calorie']",
            ".food-list",
            "[data-food]",
            "article",
            "main",
        ]
        
        print("\nSeçici testleri:")
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                print(f"  {selector}: {len(elements)} öğe")
                if elements and len(elements) > 0:
                    first = elements[0]
                    text = first.inner_text()[:100]
                    print(f"    İlk öğe: {text}")
            except Exception as e:
                print(f"  {selector}: Hata - {e}")
        
        input("Devam etmek için Enter'a basın...")
        browser.close()

if __name__ == "__main__":
    test_diyetkolik()
