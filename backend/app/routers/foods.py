# Besin Öğesi Router'ı
# GET /search?q={term}  → FTS5 ile besin araması
# POST /scrape          → Manuel scraping tetikle
# POST /manual          → Manuel besin ekleme

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FoodItem
from app.schemas import FoodItemSchema, ScrapeResult
from app.playwright_scraper import PlaywrightScraperService
from app.cache import cache

router = APIRouter()


class ManualFoodCreate(BaseModel):
    name: str
    calories_per_100g: float
    protein_per_100g: float = 0.0
    carbs_per_100g: float = 0.0
    fat_per_100g: float = 0.0


@router.get("/search", response_model=List[FoodItemSchema])
async def search_foods(
    q: str = Query(..., min_length=1, description="Arama terimi"),
    limit: int = Query(default=20, ge=1, le=50, description="Sonuç sayısı"),
    db: AsyncSession = Depends(get_db),
) -> List[FoodItemSchema]:
    """Besin adı araması yapar — 24 saat cache ile."""
    # Normalize et: küçük harf, boşlukları temizle
    q_normalized = q.strip().lower()

    # Cache kontrolü — 24 saat (besin veritabanı nadiren değişir)
    cache_key = f"food_search:{q_normalized}:{limit}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    stmt = select(FoodItem).where(
        FoodItem.name.ilike(f"%{q_normalized}%")
    ).limit(limit)

    result = await db.execute(stmt)
    foods = result.scalars().all()
    food_list = [FoodItemSchema.model_validate(food) for food in foods]

    # 24 saat cache — besin aramaları tekrar tekrar yapılır
    await cache.set(cache_key, food_list, ttl=86400)

    return food_list


@router.post("/manual", response_model=FoodItemSchema, status_code=201)
async def add_manual_food(
    data: ManualFoodCreate,
    db: AsyncSession = Depends(get_db),
) -> FoodItemSchema:
    """Manuel besin öğesi ekler."""
    food = FoodItem(
        name=data.name,
        calories_per_100g=data.calories_per_100g,
        protein_per_100g=data.protein_per_100g,
        carbs_per_100g=data.carbs_per_100g,
        fat_per_100g=data.fat_per_100g,
        source_url=None,
        scraped_at=datetime.now(timezone.utc),
    )
    db.add(food)
    await db.flush()
    await db.refresh(food)
    return FoodItemSchema.model_validate(food)


@router.post("/scrape", response_model=ScrapeResult)
async def trigger_scrape(
    db: AsyncSession = Depends(get_db),
) -> ScrapeResult:
    """Manuel olarak web scraping başlatır (Playwright ile)."""
    result = await PlaywrightScraperService.scrape_all(db)
    return ScrapeResult(
        success=result.success,
        food_count=result.food_count,
        message=result.message,
        error=result.error,
    )
