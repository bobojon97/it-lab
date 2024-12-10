FROM python:3.13-slim

# Установить рабочую директорию
WORKDIR /app

# Установить зависимости системы
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Копировать зависимости проекта
COPY requirements.txt .

# Установить Python-зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копировать оставшиеся файлы проекта
COPY . .

# Копировать скрипт ожидания (wait-for-it)
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Установить переменные окружения
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Команда для запуска
CMD ["/wait-for-it.sh", "db:5432", "python3", "manage.py", "runserver", "0.0.0.0:8000"]
