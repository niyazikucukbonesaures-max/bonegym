"""
Playwright ile diyetkolik.com'dan besin verisi çeker.
JavaScript ile render edilen sayfalar için Playwright kullanır.
Her besin linkine girip detay sayfasından veri çeker.
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright, Page as SyncPage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodItem, ScrapeMetadata

logger = logging.getLogger(__name__)

BASE_URL = "https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik"
CATEGORIES = [
    "et-tavuk-balik",
    "sut-urunleri", 
    "tahillar-ekmek",
    "sebzeler",
    "meyveler",
    "kuruyemisler",
    "baklagiller",
    "yaglar",
    "tatlilar",
    "icecekler",
    "pirinc-pilav",
    "makarna",
    "bulgur",
    "patates",
    "corbalar",
    "salatalar"
]
SITE_URL = "https://www.diyetkolik.com"


@dataclass
class FoodItemData:
    """Scraping sırasında kullanılan ham besin verisi."""
    name: str
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    source_url: str


@dataclass
class ScrapeResult:
    """Scraping işleminin sonucunu özetler."""
    success: bool
    food_count: int
    message: str
    error: Optional[str] = None


class PlaywrightScraperService:
    """Playwright ile diyetkolik.com'dan besin verisi çeken servis."""

    @staticmethod
    def _scrape_sync() -> list[FoodItemData]:
        """Sync Playwright ile scraping yapar (thread'de çalışır)."""
        all_items: list[FoodItemData] = []
        
        try:
            with sync_playwright() as p:
                # Chromium browser'ı başlat (headless mode)
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Her kategoriyi dolaş
                for category in CATEGORIES:
                    category_url = f"https://www.diyetkolik.com/kac-kalori/kategori/{category}"
                    
                    try:
                        # Kategori sayfasını yükle
                        logger.info(f"Kategori sayfası yükleniyor: {category_url}")
                        page.goto(category_url, wait_until="networkidle", timeout=60000)
                        
                        # Sayfanın yüklenmesini bekle
                        page.wait_for_timeout(3000)
                        
                        # Bu kategorideki besin linklerini topla
                        food_links = PlaywrightScraperService._get_food_links(page)
                        logger.info(f"{category} kategorisinde {len(food_links)} besin linki bulundu")
                        
                        # Her besin linkine git ve detayları çek (sadece ilk 15 tanesini al)
                        for i, link in enumerate(food_links[:15]):  # Her kategoriden max 15 besin
                            try:
                                logger.info(f"[{category}] [{i+1}/{min(15, len(food_links))}] Besin detayı çekiliyor: {link}")
                                food_data = PlaywrightScraperService._scrape_food_detail(page, link)
                                if food_data:
                                    all_items.append(food_data)
                                
                                # Rate limiting - her 5 istekte bir biraz bekle
                                if (i + 1) % 5 == 0:
                                    page.wait_for_timeout(2000)
                                    
                            except Exception as exc:
                                logger.warning(f"Besin detayı çekilemedi ({link}): {exc}")
                                continue
                    
                    except Exception as exc:
                        logger.error(f"Kategori {category} işlenirken hata: {exc}")
                        continue
                
                logger.info(f"Toplam {len(all_items)} besin başarıyla çekildi")
                
                browser.close()
                
        except Exception as exc:
            logger.error(f"Scraping hatası: {exc}", exc_info=True)
            raise
        
        return all_items

    @staticmethod
    async def scrape_all(db: AsyncSession) -> ScrapeResult:
        """
        Playwright ile tüm sayfaları dolaşarak besin verilerini çeker ve DB'ye kaydeder.
        """
        try:
            # Scraping'i ayrı thread'de çalıştır (Windows asyncio subprocess sorunu için)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                all_items = await loop.run_in_executor(
                    executor,
                    PlaywrightScraperService._scrape_sync
                )
            
        except Exception as exc:
            msg = f"Scraping hatası: {exc}"
            logger.error(msg)
            return ScrapeResult(
                success=False,
                food_count=0,
                message="Scraping başarısız.",
                error=msg
            )
        
        if not all_items:
            logger.warning("Hiç besin verisi çekilemedi.")
            return ScrapeResult(
                success=False,
                food_count=0,
                message="Hiç besin verisi bulunamadı.",
                error="empty_response"
            )
        
        # Veritabanına kaydet
        saved_count = await PlaywrightScraperService._save_to_db(all_items, db)
        await PlaywrightScraperService._update_metadata(db, saved_count, status="success")
        
        return ScrapeResult(
            success=True,
            food_count=saved_count,
            message=f"{saved_count} besin başarıyla kaydedildi.",
        )

    @staticmethod
    def _get_food_links(page: SyncPage) -> List[str]:
        """Kategori sayfasındaki tüm besin linklerini toplar."""
        links = []
        
        try:
            # Tüm besin linklerini bul (href="/kac-kalori/..." olan linkler)
            elements = page.query_selector_all('a[href^="/kac-kalori/"]')
            
            for element in elements:
                href = element.get_attribute('href')
                if href and href.startswith('/kac-kalori/') and '/kategori/' not in href:
                    full_url = SITE_URL + href
                    if full_url not in links:
                        links.append(full_url)
            
            logger.info(f"{len(links)} benzersiz besin linki bulundu")
            
        except Exception as exc:
            logger.error(f"Link toplama hatası: {exc}")
        
        return links

    @staticmethod
    def _scrape_food_detail(page: SyncPage, url: str) -> Optional[FoodItemData]:
        """Besin detay sayfasından kalori ve besin değerlerini çeker."""
        try:
            # Detay sayfasını yükle
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)
            
            # Besin adını al (h1'den)
            name = None
            try:
                name_element = page.query_selector('h1')
                if name_element:
                    name_text = name_element.inner_text().strip()
                    # "Kaç Kalori?" kısmını temizle
                    name = name_text.replace(' Kaç Kalori?', '').strip()
            except:
                pass
            
            if not name:
                logger.warning(f"Besin adı bulunamadı: {url}")
                return None
            
            # Sayfanın tüm metnini al
            text = page.inner_text('body')
            
            # 100 gram için kalori değerini bul
            # "100 gramında X kalori bulunmaktadır" formatı
            calories = None
            cal_patterns = [
                r'100\s*gram[ıi]nda\s*(\d+(?:[.,]\d+)?)\s*kalori',
                r'100\s*gram[ıi]\s*(\d+(?:[.,]\d+)?)\s*kalori',
                r'100\s*gr.*?(\d+(?:[.,]\d+)?)\s*kcal',
                r'(\d+(?:[.,]\d+)?)\s*kcal',  # Sadece "163 kcal" formatı
                r'(\d+(?:[.,]\d+)?)\s*kalori',  # Sadece "163 kalori" formatı
            ]
            
            for pattern in cal_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    calories = float(match.group(1).replace(',', '.'))
                    break
            
            # Tablo formatından besin değerlerini al
            protein = None
            carbs = None
            fat = None
            
            # "Protein (g)     13.907" formatı (tabloda)
            prot_match = re.search(r'Protein\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if prot_match:
                protein = float(prot_match.group(1).replace(',', '.'))
            
            carb_match = re.search(r'Karbonhidrat\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if carb_match:
                carbs = float(carb_match.group(1).replace(',', '.'))
            
            fat_match = re.search(r'Yağ\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if fat_match:
                fat = float(fat_match.group(1).replace(',', '.'))
            
            # Alternatif format: "13.91 gram protein" (metin içinde)
            if protein is None:
                prot_alt = re.search(r'(\d+(?:[.,]\d+)?)\s*gram\s*protein', text, re.IGNORECASE)
                if prot_alt:
                    protein = float(prot_alt.group(1).replace(',', '.'))
            
            if carbs is None:
                carb_alt = re.search(r'(\d+(?:[.,]\d+)?)\s*gram\s*karbonhidrat', text, re.IGNORECASE)
                if carb_alt:
                    carbs = float(carb_alt.group(1).replace(',', '.'))
            
            if fat is None:
                fat_alt = re.search(r'(\d+(?:[.,]\d+)?)\s*gram\s*yağ', text, re.IGNORECASE)
                if fat_alt:
                    fat = float(fat_alt.group(1).replace(',', '.'))
            
            if calories is None:
                logger.warning(f"Kalori bilgisi bulunamadı: {name} ({url})")
                return None
            
            logger.info(f"✓ {name}: {calories} kcal, P:{protein}g, C:{carbs}g, F:{fat}g")
            
            return FoodItemData(
                name=name,
                calories_per_100g=calories,
                protein_per_100g=protein or 0.0,
                carbs_per_100g=carbs or 0.0,
                fat_per_100g=fat or 0.0,
                source_url=url,
            )
            
        except Exception as exc:
            logger.error(f"Detay sayfası ayrıştırma hatası ({url}): {exc}")
            return None

    @staticmethod
    def _scrape_page_sync(page: SyncPage, source_url: str) -> list[FoodItemData]:
        """Sync Playwright Page'den besin verilerini çeker."""
        items: list[FoodItemData] = []
        
        try:
            # Sayfadaki tüm besin satırlarını bul
            # Diyetkolik.com'un yapısına göre seçicileri ayarla
            
            # Olası seçiciler:
            selectors = [
                "table tbody tr",
                "div[class*='food'] div[class*='item']",
                "div[class*='calorie'] div[class*='row']",
                ".food-list .food-item",
                "[data-food-id]",
            ]
            
            rows = []
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.info(f"Seçici bulundu: {selector} ({len(elements)} öğe)")
                        rows = elements
                        break
                except Exception:
                    continue
            
            if not rows:
                # Sayfanın HTML'ini logla
                content = page.content()
                logger.warning(f"Hiç satır bulunamadı. Sayfa içeriği (ilk 1000 karakter):\n{content[:1000]}")
                return items
            
            logger.info(f"{len(rows)} satır bulundu, ayrıştırılıyor...")
            
            for row in rows:
                try:
                    # Satırdaki tüm hücreleri al
                    cells = row.query_selector_all("td, th, div[class*='cell'], span[class*='value']")
                    
                    if len(cells) < 5:
                        continue
                    
                    # İlk hücre: besin adı
                    name_text = cells[0].inner_text()
                    name = name_text.strip()
                    
                    if not name or name.lower() in ("besin", "ad", "isim", "yiyecek", ""):
                        continue
                    
                    # Diğer hücreler: kalori, protein, karbonhidrat, yağ
                    def parse_float(text: str) -> Optional[float]:
                        text = text.strip().replace(",", ".").replace("kcal", "").replace("g", "").strip()
                        if not text or text == "-":
                            return None
                        try:
                            return float(text)
                        except ValueError:
                            return None
                    
                    calories_text = cells[1].inner_text()
                    protein_text = cells[2].inner_text()
                    carbs_text = cells[3].inner_text()
                    fat_text = cells[4].inner_text()
                    
                    calories = parse_float(calories_text)
                    protein = parse_float(protein_text)
                    carbs = parse_float(carbs_text)
                    fat = parse_float(fat_text)
                    
                    if calories is None:
                        continue
                    
                    items.append(FoodItemData(
                        name=name,
                        calories_per_100g=calories,
                        protein_per_100g=protein or 0.0,
                        carbs_per_100g=carbs or 0.0,
                        fat_per_100g=fat or 0.0,
                        source_url=source_url,
                    ))
                    
                except Exception as exc:
                    logger.debug(f"Satır ayrıştırma hatası: {exc}")
                    continue
            
            logger.info(f"{len(items)} besin başarıyla ayrıştırıldı")
            
        except Exception as exc:
            logger.error(f"Sayfa ayrıştırma hatası: {exc}")
        
        return items

    @staticmethod
    async def _save_to_db(items: list[FoodItemData], db: AsyncSession) -> int:
        """Besin listesini DB'ye kaydeder (upsert)."""
        from sqlalchemy import text
        
        if not items:
            return 0
        
        now = datetime.utcnow()
        saved = 0
        
        for item in items:
            # Ada göre mevcut kaydı ara
            result = await db.execute(
                select(FoodItem).where(FoodItem.name == item.name)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.calories_per_100g = item.calories_per_100g
                existing.protein_per_100g = item.protein_per_100g
                existing.carbs_per_100g = item.carbs_per_100g
                existing.fat_per_100g = item.fat_per_100g
                existing.source_url = item.source_url
                existing.scraped_at = now
            else:
                db.add(FoodItem(
                    name=item.name,
                    calories_per_100g=item.calories_per_100g,
                    protein_per_100g=item.protein_per_100g,
                    carbs_per_100g=item.carbs_per_100g,
                    fat_per_100g=item.fat_per_100g,
                    source_url=item.source_url,
                    scraped_at=now,
                ))
            
            saved += 1
            
            # Her 50 kayıtta bir commit yap (büyük işlemleri böl)
            if saved % 50 == 0:
                await db.commit()
                logger.info(f"{saved} besin kaydedildi...")
        
        # Son commit
        await db.commit()
        
        # FTS5 tablosunu güncelle - daha güvenli yöntem
        try:
            # Önce mevcut FTS5 kayıtlarını temizle
            await db.execute(text("DELETE FROM food_search"))
            await db.commit()
            
            # Sonra yeni kayıtları ekle
            await db.execute(text("""
                INSERT INTO food_search(rowid, name)
                SELECT id, name FROM food_items
            """))
            await db.commit()
            logger.info(f"{saved} besin DB'ye kaydedildi ve FTS5 güncellendi.")
        except Exception as e:
            logger.error(f"FTS5 güncelleme hatası: {e}")
            # FTS5 hatası olsa bile devam et
        
        return saved

    @staticmethod
    async def _update_metadata(
        db: AsyncSession,
        food_count: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Scraping meta verisini günceller."""
        db.add(ScrapeMetadata(
            last_scrape_at=datetime.utcnow(),
            food_count=food_count,
            status=status,
            error_message=error_message,
        ))
        await db.flush()
