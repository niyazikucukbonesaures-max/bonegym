import asyncio
from app.database import get_db, init_db
from app.models import FoodItem
from sqlalchemy import select, func

async def check_database():
    await init_db()
    
    async for db in get_db():
        # Toplam sayı
        result = await db.execute(select(func.count()).select_from(FoodItem))
        total = result.scalar()
        print(f"Toplam besin sayısı: {total}")
        
        # İlk 10 besin
        result = await db.execute(select(FoodItem).limit(10))
        foods = result.scalars().all()
        
        print("\nİlk 10 besin:")
        for f in foods:
            print(f"  {f.id}: {f.name} - {f.calories_per_100g} kcal, {f.protein_per_100g}g protein")
        
        # Tavuk ara
        result = await db.execute(
            select(FoodItem).where(FoodItem.name.like("%tavuk%"))
        )
        tavuk_foods = result.scalars().all()
        print(f"\n'tavuk' içeren besinler: {len(tavuk_foods)}")
        for f in tavuk_foods:
            print(f"  {f.name}")
        
        break

if __name__ == "__main__":
    asyncio.run(check_database())
