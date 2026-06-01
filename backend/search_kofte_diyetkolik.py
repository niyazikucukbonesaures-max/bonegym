"""
Diyetkolik'te köfte araması yapar
"""
from playwright.sync_api import sync_playwright
import re

def search_kofte():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Arama sayfasına git
        search_url = 'https://www.diyetkolik.com/arama?q=köfte'
        print(f'Köfte araması yapılıyor: {search_url}')
        
        try:
            page.goto(search_url, timeout=30000)
            page.wait_for_timeout(3000)
            
            # Sayfa başlığını al
            title = page.title()
            print(f'Sayfa başlığı: {title}')
            
            # Arama sonuçlarını bul
            results = page.query_selector_all('a[href^="/kac-kalori/"]')
            print(f'Bulunan sonuçlar: {len(results)}')
            
            kofte_results = []
            for result in results:
                href = result.get_attribute('href')
                text = result.inner_text().strip()
                if text and 'köfte' in text.lower():
                    kofte_results.append((text, href))
            
            print(f'Köfte sonuçları: {len(kofte_results)}')
            for i, (text, href) in enumerate(kofte_results[:10]):
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
                        
                        # Protein, karb, yağ bilgilerini de al
                        prot_match = re.search(r'Protein\s*\(g\)\s*(\d+(?:[.,]\d+)?)', body_text, re.IGNORECASE)
                        carb_match = re.search(r'Karbonhidrat\s*\(g\)\s*(\d+(?:[.,]\d+)?)', body_text, re.IGNORECASE)
                        fat_match = re.search(r'Yağ\s*\(g\)\s*(\d+(?:[.,]\d+)?)', body_text, re.IGNORECASE)
                        
                        protein = prot_match.group(1) if prot_match else "?"
                        carbs = carb_match.group(1) if carb_match else "?"
                        fat = fat_match.group(1) if fat_match else "?"
                        
                        print(f'     → {calories} kcal/100g | P:{protein}g C:{carbs}g F:{fat}g')
                    else:
                        print(f'     → Kalori bilgisi bulunamadı')
                        
                except Exception as e:
                    print(f'     → Detay hatası: {e}')
                
        except Exception as e:
            print(f'Arama hatası: {e}')
        
        browser.close()

if __name__ == "__main__":
    search_kofte()