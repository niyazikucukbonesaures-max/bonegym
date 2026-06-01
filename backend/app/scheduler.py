# Fitness ve Kalori Takip Uygulaması - APScheduler Zamanlayıcı
# 24 saatlik interval ile ScraperService.scrape_all() çağrısını zamanlar.

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import AsyncSessionLocal
from app.scraper import ScraperService

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


async def _run_scrape_job() -> None:
    """Zamanlayıcı tarafından tetiklenen scraping görevi."""
    logger.info("Zamanlanmış scraping görevi başlatılıyor...")
    async with AsyncSessionLocal() as session:
        try:
            result = await ScraperService.scrape_all(session)
            if result.success:
                logger.info("Zamanlanmış scraping tamamlandı: %s", result.message)
            else:
                logger.warning("Zamanlanmış scraping başarısız: %s", result.error)
        except Exception as exc:  # noqa: BLE001
            logger.error("Zamanlanmış scraping sırasında beklenmeyen hata: %s", exc)


def start_scheduler() -> None:
    """Scheduler'ı başlatır ve 24 saatlik scraping görevini ekler."""
    _scheduler.add_job(
        _run_scrape_job,
        trigger="interval",
        hours=24,
        id="scrape_job",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler başlatıldı — scraping görevi 24 saatte bir çalışacak.")


def stop_scheduler() -> None:
    """Scheduler'ı durdurur."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler durduruldu.")


def get_scheduler() -> AsyncIOScheduler:
    """Scheduler örneğini döner (test ve doğrulama için)."""
    return _scheduler
