"""
Tek bir besin sayfasını detaylı inceler.
"""
from playwright.sync_api import sync_playwright

def test_single_food():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        url = "https://www.diyetkolik.com/kac-kalori/adana-durum"
        print(f"Sayfa yükleniyor: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Screenshot al
        page.screenshot(path="tavuk_gogsu.png")
        print("Screenshot kaydedildi: tavuk_gogsu.png")
        
        # HTML'i kaydet
        content = page.content()
        with open("tavuk_gogsu.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML kaydedildi: tavuk_gogsu.html")
        
        # Sayfadaki tüm metni göster
        text = page.inner_text('body')
        print("\n=== SAYFA METNİ (İlk 2000 karakter) ===")
        print(text[:2000])
        
        # Besin değerlerini içeren elementleri bul
        print("\n=== BESİN DEĞERLERİ ARAŞTIRMASI ===")
        
        # Olası seçiciler
        selectors = [
            'div[class*="nutrition"]',
            'div[class*="besin"]',
            'div[class*="kalori"]',
            'table',
            'dl',
            'ul',
        ]
        
        for selector in selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"\n{selector}: {len(elements)} öğe bulundu")
                for i, elem in enumerate(elements[:2]):
                    text = elem.inner_text()[:200]
                    print(f"  [{i}]: {text}")
        
        input("\nDevam etmek için Enter'a basın...")
        browser.close()

if __name__ == "__main__":
    test_single_food()
