"""
Diyetkolik'te pilav araması yapar
"""
from playwright.sync_api import sync_playwright
import re

def search_pilav():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Arama sayfasına git
        search_url = 'https://www.diyetkolik.com/arama?q=pilav'
        print(f'Arama yapılıyor: {search_url}')
        
        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_timeout(3000)
            
            # Sayfa başlığını al
            title = page.title()
            print(f'Sayfa başlığı: {title}')
            
            # Arama sonuçlarını bul
            results = page.query_selector_all('a[href^="/kac-kalori/"]')
            print(f'Bulunan sonuçlar: {len(results)}')
            
            pilav_results = []
            for result in results:
                href = result.get_attribute('href')
                text = result.inner_text().strip()
                if text and 'pilav' in text.lower():
                    pilav_results.append((text, href))
            
            print(f'Pilav sonuçları: {len(pilav_results)}')
            for i, (text, href) in enumerate(pilav_results[:5]):
                print(f'  {i+1}. {text}')
                
                # Detay sayfasına git
                detail_url = f"https://www.diyetkolik.com{href}"
                try:
                    page.goto(detail_url, timeout=15000)
                    page.wait_for_timeout(1000)
                    
                    # Kalori bilgisini bul
                    body_text = page.inner_text('body')
                    
                    # Kalori regex'i
                    cal_match = re.search(r'100\s*gram[ıi]nda\s*(\d+(?:[.,]\d+)?)\s*kalori', body_text, re.IGNORECASE)
                    if cal_match:
                        calories = cal_match.group(1)
                        print(f'     → {calories} kcal/100g')
                    else:
                        print(f'     → Kalori bilgisi bulunamadı')
                        
                except Exception as e:
                    print(f'     → Detay hatası: {e}')
                
        except Exception as e:
            print(f'Arama hatası: {e}')
        
        browser.close()

if __name__ == "__main__":
    search_pilav()