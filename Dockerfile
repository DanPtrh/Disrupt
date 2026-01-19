# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot/ ./bot/

# Создаем директорию для данных
RUN mkdir -p bot/data

# Запускаем бота
CMD ["python", "-m", "bot.app"]
