"""
Backend başlatma scripti.
Geliştirme: python start.py
Production: python start.py --prod
"""
import os
import sys
import multiprocessing
import uvicorn


def get_worker_count() -> int:
    """CPU sayısına göre worker sayısını belirle."""
    cpu_count = multiprocessing.cpu_count()
    # Formül: (2 × CPU) + 1, max 8
    return min((2 * cpu_count) + 1, 8)


if __name__ == "__main__":
    is_prod = "--prod" in sys.argv
    workers = get_worker_count() if is_prod else 1

    print(f"🚀 Backend başlatılıyor — {'Production' if is_prod else 'Development'} modu")
    print(f"   Workers: {workers}")
    print(f"   Port: 8000")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=workers,
        reload=not is_prod,
        log_level="info" if is_prod else "debug",
        # SQLite için önemli: her worker kendi bağlantısını kullansın
        loop="asyncio",
    )
