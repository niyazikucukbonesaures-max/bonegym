"""
Diyetkolik.com'dan daha fazla tavuk pilavı çeşidi scrape eder
"""
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright
from app.database import get_db
from app.models import FoodItem
from sqlalchemy import select

async def scrape_tavuk_pilav_from_diyetkolik():
    """Diyetkolik'ten tavuk pilavı çeşitlerini scrape eder."""
    
    # Tavuk pilavı ile ilgili arama terimleri
    search_terms = [
        "tavuk pilav",
        "tavuklu pilav", 
        "chicken rice",
        "pilav tavuk",
        "tavuk pirinç"
    ]
    
    scraped_foods = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for term in search_terms:
            print(f"🔍 Aranan terim: {term}")
            
            try:
                # Arama sayfasına git
                search_url = f"https://www.diyetkolik.com/arama?q={term.replace(' ', '+')}"
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                
                # Arama sonuçlarındaki linkleri bul
                food_links = await page.query_selector_all('a[href*="/kac-kalori/"]')
                
                for link in food_links[:5]:  # Her terim için ilk 5 sonuç
                    try:
                        href = await link.get_attribute('href')
                        if not href:
                            continue
                            
                        full_url = f"https://www.diyetkolik.com{href}" if href.startswith('/') else href
                        
                        # Detay sayfasına git
                        await page.goto(full_url, wait_until="networkidle", timeout=30000)
                        
                        # Besin adını al
                        name_element = await page.query_selector('h1')
                        if not name_element:
                            continue
                            
                        name = (await name_element.inner_text()).strip()
                        
                        # Sadece tavuk pilavı ile ilgili olanları al
                        if not any(keyword in name.lower() for keyword in ['tavuk', 'chicken', 'pilav', 'rice']):
                            continue
                            
                        # Sayfa içeriğini al
                        content = await page.content()
                        
                        # Kalori bilgisini bul
                        calorie_patterns = [
                            r'100\s*gram[ıi]nda\s*(\d+(?:[.,]\d+)?)\s*kalori',
                            r'100\s*gram[ıi]\s*(\d+(?:[.,]\d+)?)\s*kalori',
                            r'(\d+(?:[.,]\d+)?)\s*kalori.*100\s*gram',
                            r'Kalori[:\s]*(\d+(?:[.,]\d+)?)',
                        ]
                        
                        calories = None
                        for pattern in calorie_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                calories = float(match.group(1).replace(',', '.'))
                                break
                        
                        if not calories:
                            continue
                        
                        # Protein, karbonhidrat, yağ bilgilerini bul
                        protein_match = re.search(r'Protein[^0-9]*(\d+(?:[.,]\d+)?)', content, re.IGNORECASE)
                        carbs_match = re.search(r'Karbonhidrat[^0-9]*(\d+(?:[.,]\d+)?)', content, re.IGNORECASE)
                        fat_match = re.search(r'Yağ[^0-9]*(\d+(?:[.,]\d+)?)', content, re.IGNORECASE)
                        
                        protein = float(protein_match.group(1).replace(',', '.')) if protein_match else 0
                        carbs = float(carbs_match.group(1).replace(',', '.')) if carbs_match else 0
                        fat = float(fat_match.group(1).replace(',', '.')) if fat_match else 0
                        
                        food_data = {
                            'name': name,
                            'calories': calories,
                            'protein': protein,
                            'carbs': carbs,
                            'fat': fat,
                            'url': full_url
                        }
                        
                        # Aynı isimde zaten var mı kontrol et
                        if not any(f['name'] == name for f in scraped_foods):
                            scraped_foods.append(food_data)
                            print(f"✅ {name}: {calories} kcal")
                        
                    except Exception as e:
                        print(f"❌ Link işlenirken hata: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Arama terimi '{term}' işlenirken hata: {e}")
                continue
        
        await browser.close()
    
    return scraped_foods

async def add_scraped_tavuk_pilav():
    """Scrape edilen tavuk pilavı verilerini veritabanına ekler."""
    
    # Önce scrape et
    print("🔍 Diyetkolik'ten tavuk pilavı çeşitleri aranıyor...")
    scraped_foods = await scrape_tavuk_pilav_from_diyetkolik()
    
    if not scraped_foods:
        print("❌ Hiç tavuk pilavı bulunamadı!")
        return
    
    print(f"\n📊 {len(scraped_foods)} tavuk pilavı çeşidi bulundu!")
    
    # Veritabanına ekle
    async for db in get_db():
        now = datetime.utcnow()
        added = 0
        updated = 0
        
        for food_data in scraped_foods:
            # Mevcut kaydı kontrol et
            result = await db.execute(
                select(FoodItem).where(FoodItem.name == food_data['name'])
            )
            food = result.scalar_one_or_none()
            
            if food:
                # Güncelle
                old_calories = food.calories_per_100g
                food.calories_per_100g = food_data['calories']
                food.protein_per_100g = food_data['protein']
                food.carbs_per_100g = food_data['carbs']
                food.fat_per_100g = food_data['fat']
                food.source_url = "diyetkolik_verified"
                updated += 1
                print(f"🔄 {food_data['name']}: {old_calories} → {food_data['calories']} kcal (güncellendi)")
            else:
                # Yeni ekle
                new_food = FoodItem(
                    name=food_data['name'],
                    calories_per_100g=food_data['calories'],
                    protein_per_100g=food_data['protein'],
                    carbs_per_100g=food_data['carbs'],
                    fat_per_100g=food_data['fat'],
                    source_url="diyetkolik_verified",
                    scraped_at=now,
                )
                db.add(new_food)
                added += 1
                print(f"🆕 {food_data['name']}: {food_data['calories']} kcal (yeni eklendi)")
        
        await db.commit()
        print(f"\n🎯 {updated} tavuk pilavı güncellendi, {added} yeni tavuk pilavı çeşidi eklendi!")
        print(f"📊 Toplam işlenen: {len(scraped_foods)} çeşit")
        break

if __name__ == "__main__":
    asyncio.run(add_scraped_tavuk_pilav())