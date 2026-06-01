import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_scrape():
    url = "https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik"
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        print(f"Fetching: {url}")
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Tüm tabloları bul
        tables = soup.find_all("table")
        print(f"\nToplam tablo sayısı: {len(tables)}")
        
        # Tüm satırları bul
        all_rows = soup.find_all("tr")
        print(f"Toplam tr sayısı: {len(all_rows)}")
        
        # İlk 5 satırı göster
        print("\nİlk 5 satır:")
        for i, row in enumerate(all_rows[:5]):
            cells = row.find_all(["td", "th"])
            print(f"Satır {i}: {len(cells)} hücre")
            if cells:
                print(f"  İçerik: {[c.get_text(strip=True)[:30] for c in cells[:5]]}")
        
        # Besin listesi için olası seçiciler
        print("\n--- Olası seçiciler ---")
        print(f"div.food-item: {len(soup.select('div.food-item'))}")
        print(f"div.calorie-item: {len(soup.select('div.calorie-item'))}")
        print(f"li.food: {len(soup.select('li.food'))}")
        print(f"div[class*='food']: {len(soup.select('div[class*=\"food\"]'))}")
        print(f"div[class*='calorie']: {len(soup.select('div[class*=\"calorie\"]'))}")
        
        # Sayfa yapısını göster
        print("\n--- Sayfa yapısı (ilk 2000 karakter) ---")
        print(resp.text[:2000])

if __name__ == "__main__":
    asyncio.run(test_scrape())
