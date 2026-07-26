FROM python:3.14-slim

WORKDIR /app

# Нужно для ZoneInfo(Europe/Moscow) и напоминаний в 10:00
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Moscow

CMD ["python", "bot.py"]
