"""
Diyetkolik'te pilav kategorisini kontrol eder
"""
from playwright.sync_api import sync_playwright

def test_pilav_category():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Pilav kategorisini kontrol et
        url = 'https://www.diyetkolik.com/kac-kalori/kategori/pirinc-pilav'
        print(f'Kontrol ediliyor: {url}')
        
        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)
            
            # Sayfa başlığını al
            title = page.title()
            print(f'Sayfa başlığı: {title}')
            
            # Besin linklerini bul
            links = page.query_selector_all('a[href^="/kac-kalori/"]')
            print(f'Bulunan linkler: {len(links)}')
            
            pilav_links = []
            for link in links:
                href = link.get_attribute('href')
                text = link.inner_text().strip()
                if text and ('pilav' in text.lower() or 'pirinç' in text.lower()):
                    pilav_links.append((text, href))
            
            print(f'Pilav ile ilgili linkler: {len(pilav_links)}')
            for i, (text, href) in enumerate(pilav_links[:10]):
                print(f'  {i+1}. {text} -> {href}')
                
        except Exception as e:
            print(f'Hata: {e}')
        
        browser.close()

if __name__ == "__main__":
    test_pilav_category()