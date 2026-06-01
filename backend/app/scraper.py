# Fitness ve Kalori Takip Uygulaması - Web Scraper Servisi
# diyetkolik.com'dan besin kalori verilerini çeker ve yerel DB'ye kaydeder.
# JavaScript ile render edilen sayfalar için Playwright kullanır.

import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import Page as SyncPage, sync_playwright
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FoodItem, ScrapeMetadata

logger = logging.getLogger(__name__)

BASE_URL = "https://www.diyetkolik.com/kac-kalori/kategori/et-tavuk-balik"
SITE_URL = "https://www.diyetkolik.com"


# ---------------------------------------------------------------------------
# Veri sınıfları
# ---------------------------------------------------------------------------

@dataclass
class FoodItemData:
    """Scraping sırasında kullanılan ham besin verisi (Pydantic değil, saf dataclass)."""
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


# ---------------------------------------------------------------------------
# ScraperService
# ---------------------------------------------------------------------------

class ScraperService:
    """diyetkolik.com'dan besin verisi çeken ve yerel DB'ye kaydeden servis."""

    # ---------------------------------------------------------------------------
    # Genel scraping akışı
    # ---------------------------------------------------------------------------

    @staticmethod
    async def scrape_all(db: AsyncSession) -> ScrapeResult:
        """
        Playwright ile tüm sayfaları dolaşarak besin verilerini çeker ve DB'ye kaydeder.
        HTTP/ağ hatası durumunda mevcut DB korunur; metadata güncellenmez.
        """
        try:
            # Scraping'i ayrı thread'de çalıştır (Windows asyncio subprocess sorunu için)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                all_items = await loop.run_in_executor(
                    executor,
                    ScraperService._scrape_sync
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
        saved_count = await ScraperService.save_to_db(all_items, db)
        await ScraperService._update_metadata(db, saved_count, status="success")
        
        return ScrapeResult(
            success=True,
            food_count=saved_count,
            message=f"{saved_count} besin başarıyla kaydedildi.",
        )

    @staticmethod
    def _scrape_sync() -> List[FoodItemData]:
        """Sync Playwright ile scraping yapar (thread'de çalışır)."""
        all_items: List[FoodItemData] = []
        
        try:
            with sync_playwright() as p:
                # Chromium browser'ı başlat (headless mode)
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Ana kategori sayfasını yükle
                logger.info(f"Ana sayfa yükleniyor: {BASE_URL}")
                page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
                
                # Sayfanın yüklenmesini bekle
                page.wait_for_timeout(3000)
                
                # Bu kategorideki besin linklerini topla
                food_links = ScraperService._get_food_links(page)
                logger.info(f"Et-tavuk-balık kategorisinde {len(food_links)} besin linki bulundu")
                
                # Her besin linkine git ve detayları çek (ilk 50 tanesini al)
                for i, link in enumerate(food_links[:50]):
                    try:
                        logger.info(f"[{i+1}/{min(50, len(food_links))}] Besin detayı çekiliyor: {link}")
                        food_data = ScraperService._scrape_food_detail(page, link)
                        if food_data:
                            all_items.append(food_data)
                        
                        # Rate limiting - her 5 istekte bir biraz bekle
                        if (i + 1) % 5 == 0:
                            page.wait_for_timeout(2000)
                            
                    except Exception as exc:
                        logger.warning(f"Besin detayı çekilemedi ({link}): {exc}")
                        continue
                
                logger.info(f"Toplam {len(all_items)} besin başarıyla çekildi")
                
                browser.close()
                
        except Exception as exc:
            logger.error(f"Scraping hatası: {exc}", exc_info=True)
            raise
        
        return all_items

    # ---------------------------------------------------------------------------
    # Tek sayfa çekme (Playwright ile)
    # ---------------------------------------------------------------------------

    @staticmethod
    async def scrape_page(
        url: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> List[FoodItemData]:
        """
        Verilen URL'deki besin listesini Playwright ile çeker ve ayrıştırır.
        JavaScript ile render edilen sayfalar için Playwright kullanır.
        """
        try:
            # Scraping'i ayrı thread'de çalıştır
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                items = await loop.run_in_executor(
                    executor,
                    ScraperService._scrape_page_sync,
                    url
                )
            return items
        except Exception as exc:
            logger.error(f"Sayfa çekme hatası ({url}): {exc}")
            return []

    @staticmethod
    def _scrape_page_sync(url: str) -> List[FoodItemData]:
        """Sync Playwright ile tek sayfa çeker."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)
                
                # Besin linklerini topla
                food_links = ScraperService._get_food_links(page)
                items = []
                
                # İlk 10 besin detayını çek
                for link in food_links[:10]:
                    try:
                        food_data = ScraperService._scrape_food_detail(page, link)
                        if food_data:
                            items.append(food_data)
                    except Exception as exc:
                        logger.warning(f"Besin detayı çekilemedi ({link}): {exc}")
                        continue
                
                browser.close()
                return items
                
        except Exception as exc:
            logger.error(f"Sync sayfa çekme hatası ({url}): {exc}")
            return []

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
            calories = None
            cal_patterns = [
                r'100\s*gram[ıi]nda\s*(\d+(?:[.,]\d+)?)\s*kalori',
                r'100\s*gram[ıi]\s*(\d+(?:[.,]\d+)?)\s*kalori',
                r'100\s*gr.*?(\d+(?:[.,]\d+)?)\s*kcal',
                r'(\d+(?:[.,]\d+)?)\s*kcal',
                r'(\d+(?:[.,]\d+)?)\s*kalori',
            ]
            
            for pattern in cal_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    calories = float(match.group(1).replace(',', '.'))
                    break
            
            # Besin değerlerini al
            protein = None
            carbs = None
            fat = None
            
            # Tablo formatından besin değerlerini al
            prot_match = re.search(r'Protein\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if prot_match:
                protein = float(prot_match.group(1).replace(',', '.'))
            
            carb_match = re.search(r'Karbonhidrat\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if carb_match:
                carbs = float(carb_match.group(1).replace(',', '.'))
            
            fat_match = re.search(r'Yağ\s*\(g\)\s*(\d+(?:[.,]\d+)?)', text, re.IGNORECASE)
            if fat_match:
                fat = float(fat_match.group(1).replace(',', '.'))
            
            # Alternatif format: "13.91 gram protein"
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

    # ---------------------------------------------------------------------------
    # Veritabanı işlemleri
    # ---------------------------------------------------------------------------

    @staticmethod
    async def save_to_db(items: list[FoodItemData], db: AsyncSession) -> int:
        """
        Besin listesini DB'ye kaydeder.
        Mevcut kayıtları günceller (upsert: ada göre eşleştirme).
        Kaydedilen toplam sayıyı döner.
        """
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

        await db.flush()
        logger.info("%d besin DB'ye kaydedildi.", saved)
        return saved

    # ---------------------------------------------------------------------------
    # Meta veri
    # ---------------------------------------------------------------------------

    @staticmethod
    async def get_last_scrape_info(db: AsyncSession) -> Optional[ScrapeMetadata]:
        """Son scraping meta verisini döner. Hiç scraping yapılmadıysa None döner."""
        result = await db.execute(
            select(ScrapeMetadata).order_by(ScrapeMetadata.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _update_metadata(
        db: AsyncSession,
        food_count: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Scraping meta verisini günceller (yeni kayıt ekler)."""
        db.add(ScrapeMetadata(
            last_scrape_at=datetime.utcnow(),
            food_count=food_count,
            status=status,
            error_message=error_message,
        ))
        await db.flush()
