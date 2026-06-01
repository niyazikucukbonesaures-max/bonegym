"""
Diyetkolik.com'dan besin çekme testini yapar.
İlk 5 besini test eder.
"""
from playwright.sync_api import sync_playwright
import re

def test_full_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Kategori sayfasını yükle
        url = "https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik"
        print(f"Kategori sayfası yükleniyor: {url}")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Tüm besin linklerini topla
        elements = page.query_selector_all('a[href^="/kac-kalori/"]')
        links = []
        for element in elements:
            href = element.get_attribute('href')
            if href and href.startswith('/kac-kalori/') and '/kategori/' not in href:
                full_url = "https://www.diyetkolik.com" + href
                if full_url not in links:
                    links.append(full_url)
        
        print(f"\n{len(links)} benzersiz besin linki bulundu")
        print(f"İlk 5 besini test ediyoruz...\n")
        
        # İlk 5 besini test et
        for i, link in enumerate(links[:5]):
            print(f"\n[{i+1}/5] {link}")
            try:
                page.goto(link, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1000)
                
                # Besin adı
                name = None
                try:
                    name_element = page.query_selector('h1')
                    if name_element:
                        name = name_element.inner_text().strip()
                except:
                    pass
                
                print(f"  Besin: {name}")
                
                # Sayfanın içeriğini al
                content = page.content()
                
                # Kalori
                cal_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kcal|kalori)', content, re.IGNORECASE)
                calories = float(cal_match.group(1).replace(',', '.')) if cal_match else None
                
                # Protein
                prot_match = re.search(r'Protein[:\s]*(\d+(?:[.,]\d+)?)\s*g', content, re.IGNORECASE)
                protein = float(prot_match.group(1).replace(',', '.')) if prot_match else None
                
                # Karbonhidrat
                carb_match = re.search(r'Karbonhidrat[:\s]*(\d+(?:[.,]\d+)?)\s*g', content, re.IGNORECASE)
                carbs = float(carb_match.group(1).replace(',', '.')) if carb_match else None
                
                # Yağ
                fat_match = re.search(r'Yağ[:\s]*(\d+(?:[.,]\d+)?)\s*g', content, re.IGNORECASE)
                fat = float(fat_match.group(1).replace(',', '.')) if fat_match else None
                
                print(f"  Kalori: {calories} kcal")
                print(f"  Protein: {protein} g")
                print(f"  Karbonhidrat: {carbs} g")
                print(f"  Yağ: {fat} g")
                
                if calories:
                    print(f"  ✓ Başarılı!")
                else:
                    print(f"  ✗ Kalori bulunamadı")
                    # Sayfanın bir kısmını göster
                    text = page.inner_text('body')[:500]
                    print(f"  Sayfa içeriği: {text}")
                
            except Exception as e:
                print(f"  ✗ Hata: {e}")
        
        input("\nDevam etmek için Enter'a basın...")
        browser.close()

if __name__ == "__main__":
    test_full_scraper()
