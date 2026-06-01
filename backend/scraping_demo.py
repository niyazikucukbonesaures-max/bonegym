#!/usr/bin/env python3
"""
Web Scraping Demo - Gerçek sitelerde nasıl veri bulunur
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

async def demo_diyetkolik_search():
    """Diyetkolik'te gerçek arama demo'su."""
    
    print("🔍 Diyetkolik.com'da 'tavuk göğsü' aranıyor...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Ana sayfayı kontrol et
        try:
            async with session.get('https://www.diyetkolik.com') as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    print("✅ Diyetkolik.com'a bağlanıldı")
                    
                    # Arama formu var mı?
                    search_forms = soup.find_all('form')
                    search_inputs = soup.find_all('input', {'type': 'search'})
                    
                    print(f"📋 {len(search_forms)} form bulundu")
                    print(f"🔍 {len(search_inputs)} arama kutusu bulundu")
                    
                    # Besin değerleri linki var mı?
                    nutrition_links = soup.find_all('a', href=re.compile(r'besin|kalori|değer', re.I))
                    print(f"🥗 {len(nutrition_links)} besin linki bulundu")
                    
                    for link in nutrition_links[:3]:
                        print(f"  - {link.get_text(strip=True)}: {link.get('href')}")
                
        except Exception as e:
            print(f"❌ Diyetkolik bağlantı hatası: {e}")

async def demo_beslenme_gov():
    """Beslenme.gov.tr demo'su."""
    
    print("\n🏛️ Beslenme.gov.tr kontrol ediliyor...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get('https://beslenme.gov.tr') as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    print("✅ Beslenme.gov.tr'ye bağlanıldı")
                    
                    # Besin veritabanı linki ara
                    db_links = soup.find_all('a', href=re.compile(r'veritaban|besin|tablo', re.I))
                    print(f"📊 {len(db_links)} veritabanı linki bulundu")
                    
                    for link in db_links[:3]:
                        print(f"  - {link.get_text(strip=True)}: {link.get('href')}")
                
        except Exception as e:
            print(f"❌ Beslenme.gov.tr bağlantı hatası: {e}")

async def demo_generic_search():
    """Genel besin sitelerini demo et."""
    
    print("\n🌐 Genel Türk besin siteleri kontrol ediliyor...")
    
    sites_to_check = [
        'https://hsgm.saglik.gov.tr',
        'https://www.hacettepe.edu.tr',
        'https://gida.tarimorman.gov.tr'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for site_url in sites_to_check:
            try:
                print(f"\n🔍 {site_url} kontrol ediliyor...")
                
                async with session.get(site_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        print(f"✅ {site_url} erişilebilir")
                        
                        # Besin/beslenme ile ilgili linkler ara
                        nutrition_keywords = ['besin', 'beslenme', 'kalori', 'gıda', 'nutrition']
                        found_links = []
                        
                        for keyword in nutrition_keywords:
                            links = soup.find_all('a', href=re.compile(keyword, re.I))
                            found_links.extend(links)
                        
                        # Tekrarları kaldır
                        unique_links = {}
                        for link in found_links:
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            if href and text and len(text) > 3:
                                unique_links[href] = text
                        
                        print(f"🥗 {len(unique_links)} besin linki bulundu")
                        
                        # İlk 3'ünü göster
                        for i, (href, text) in enumerate(list(unique_links.items())[:3]):
                            print(f"  {i+1}. {text}: {href}")
                    
                    else:
                        print(f"❌ {site_url} erişilemez (Status: {response.status})")
                        
            except Exception as e:
                print(f"❌ {site_url} hatası: {e}")

async def demo_html_parsing():
    """HTML parsing demo'su - Besin değerlerini nasıl çıkarırız."""
    
    print("\n🧩 HTML Parsing Demo - Besin değerlerini çıkarma")
    print("=" * 50)
    
    # Örnek HTML (gerçek sitelerden alınmış yapı)
    sample_html = """
    <div class="food-details">
        <h2>Tavuk Göğsü (Haşlanmış)</h2>
        <table class="nutrition-table">
            <tr><td>Kalori</td><td>165 kcal</td></tr>
            <tr><td>Protein</td><td>31.0 g</td></tr>
            <tr><td>Karbonhidrat</td><td>0.0 g</td></tr>
            <tr><td>Yağ</td><td>3.6 g</td></tr>
        </table>
        
        <div class="nutrition-info">
            <p>100 gram tavuk göğsünde 165 kalori bulunur.</p>
            <p>Protein miktarı: 31 gram</p>
            <p>Karbonhidrat: 0 gram, Yağ: 3.6 gram</p>
        </div>
    </div>
    """
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    print("📄 Örnek HTML:")
    print(sample_html)
    
    print("\n🔍 Parsing Sonuçları:")
    
    # 1. Tablo yapısından çıkar
    print("\n1️⃣ Tablo yapısından çıkarma:")
    table_rows = soup.find_all('tr')
    for row in table_rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            nutrient = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            print(f"   {nutrient}: {value}")
    
    # 2. Regex ile text'ten çıkar
    print("\n2️⃣ Regex ile text'ten çıkarma:")
    all_text = soup.get_text()
    
    patterns = {
        'Kalori': r'(\d+(?:\.\d+)?)\s*(?:kcal|kalori)',
        'Protein': r'protein[:\s]*(\d+(?:\.\d+)?)',
        'Karbonhidrat': r'karbonhidrat[:\s]*(\d+(?:\.\d+)?)',
        'Yağ': r'yağ[:\s]*(\d+(?:\.\d+)?)'
    }
    
    for nutrient, pattern in patterns.items():
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            print(f"   {nutrient}: {value}")

async def main():
    """Ana demo fonksiyonu."""
    
    print("🕷️ Web Scraping Demo Başlatılıyor")
    print("=" * 60)
    
    # 1. Sitelere bağlantı testi
    await demo_diyetkolik_search()
    await demo_beslenme_gov()
    await demo_generic_search()
    
    # 2. HTML parsing demo
    await demo_html_parsing()
    
    print("\n✅ Demo tamamlandı!")
    print("\n💡 Önemli Notlar:")
    print("   - Gerçek siteler farklı yapıda olabilir")
    print("   - Rate limiting önemli (1-2 saniye bekle)")
    print("   - User-Agent header'ı gerekli")
    print("   - Hata yönetimi kritik")

if __name__ == "__main__":
    asyncio.run(main())