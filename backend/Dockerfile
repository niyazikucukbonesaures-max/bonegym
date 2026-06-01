FROM python:3.12-slim

WORKDIR /app

# Sistem bağımlılıkları (asyncpg için libpq, derleme için gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları önce kopyala — Docker layer cache optimizasyonu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala (.env ve *.db hariç — .dockerignore ile)
COPY app/ ./app/

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production: tek worker, async loop
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
