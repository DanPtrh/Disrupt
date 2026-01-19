#!/bin/bash
# Скрипт инициализации JSON файлов базы данных

DATA_DIR="bot/data"

# Создаем директорию если её нет
mkdir -p "$DATA_DIR"

# Инициализируем JSON файлы пустыми массивами, если они не существуют
for file in users.json teams.json rounds.json solutions.json moderators.json; do
    if [ ! -f "$DATA_DIR/$file" ]; then
        echo "[]" > "$DATA_DIR/$file"
        echo "Создан файл: $DATA_DIR/$file"
    else
        echo "Файл уже существует: $DATA_DIR/$file"
    fi
done

echo "Инициализация завершена!"
