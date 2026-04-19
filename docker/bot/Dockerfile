FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1️⃣ Сначала зависимости (кэшируемый слой)
COPY requirements.txt pyproject.toml README.md ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt 

# 2️⃣ Потом код (часто меняется)
COPY src ./src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "support_bot.bot.main"]