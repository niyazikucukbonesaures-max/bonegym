# Scheduler konfigürasyon smoke testleri
# Scheduler'ın doğru interval ile konfigüre edildiğini doğrular.

import pytest

from app.scheduler import get_scheduler, start_scheduler, stop_scheduler


@pytest.mark.asyncio
async def test_scheduler_job_configured_with_24h_interval():
    """Scheduler'ın 24 saatlik interval ile konfigüre edildiğini doğrular."""
    start_scheduler()
    scheduler = get_scheduler()

    try:
        jobs = scheduler.get_jobs()
        assert len(jobs) >= 1, "En az bir zamanlama görevi olmalı"

        scrape_job = next((j for j in jobs if j.id == "scrape_job"), None)
        assert scrape_job is not None, "scrape_job bulunamadı"

        # Trigger interval kontrolü
        trigger = scrape_job.trigger
        assert trigger is not None

        # APScheduler IntervalTrigger'ın interval değerini kontrol et
        interval_seconds = trigger.interval.total_seconds()
        assert interval_seconds == 24 * 3600, (
            f"Beklenen interval: {24 * 3600}s, gerçek: {interval_seconds}s"
        )
    finally:
        stop_scheduler()


@pytest.mark.asyncio
async def test_scheduler_starts_and_stops():
    """Scheduler'ın başlatılıp durdurulabildiğini doğrular."""
    start_scheduler()
    scheduler = get_scheduler()
    assert scheduler.running, "Scheduler çalışıyor olmalı"

    # stop_scheduler çağrısı hata vermemeli
    stop_scheduler()
    # İkinci kez çağrı da güvenli olmalı (idempotent)
    stop_scheduler()
