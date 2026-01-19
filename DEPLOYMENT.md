# Инструкция по развертыванию бота "Дизрапт"

## Подготовка сервера

### Требования
- Ubuntu 20.04 или выше / Debian 11 или выше
- Минимум 1 GB RAM
- Docker и Docker Compose
- Доступ к интернету

### Установка Docker

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться для применения изменений
newgrp docker
```

## Развертывание бота

### 1. Загрузка проекта на сервер

#### Вариант А: Через Git (рекомендуется)

```bash
# Установка git если нужно
sudo apt install -y git

# Клонирование репозитория
git clone <repository-url>
cd Disrupt
```

#### Вариант Б: Загрузка архива

```bash
# На локальной машине создайте архив
cd "Disrupt"
tar -czf disrupt-bot.tar.gz --exclude='.git' --exclude='bot/data' --exclude='__pycache__' .

# Передайте на сервер через scp
scp disrupt-bot.tar.gz user@server:/home/user/

# На сервере распакуйте
cd /home/user
tar -xzf disrupt-bot.tar.gz
cd Disrupt
```

### 2. Настройка переменных окружения

```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

**Обязательные параметры для заполнения:**

```env
# Токен бота от @BotFather
BOT_TOKEN=8482954136:AAHcL6eTMYMmSKyT-v7H8mDwA1L2FgUA2PU

# Telegram user_id администраторов (узнать у @userinfobot)
ADMINS=[123456789,987654321]

# GigaChat credentials (получить на developers.sber.ru)
GIGACHAT_CREDENTIALS=your_base64_credentials
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_VERIFY_SSL=false
```

### 3. Запуск бота

#### Простой запуск (development)

```bash
# Автоматическое развертывание
./deploy.sh
```

#### Production запуск

```bash
# Инициализация базы данных
./init_data.sh

# Запуск в production режиме
docker-compose -f docker-compose.prod.yml up -d --build

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Проверка работы

```bash
# Проверка статуса контейнера
docker-compose ps

# Просмотр логов
docker-compose logs --tail=50 -f

# Проверка использования ресурсов
docker stats
```

## Управление ботом

### Остановка

```bash
docker-compose down
```

### Перезапуск

```bash
docker-compose restart
```

### Обновление

```bash
# Остановка
docker-compose down

# Обновление кода (если через git)
git pull

# Или загрузка нового архива и распаковка

# Пересборка и запуск
docker-compose up -d --build
```

### Просмотр логов

```bash
# Последние 100 строк
docker-compose logs --tail=100

# В реальном времени
docker-compose logs -f

# Только ошибки
docker-compose logs | grep ERROR
```

## Резервное копирование

### Создание backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Создание архива данных
tar -czf "$BACKUP_DIR/disrupt-data-$DATE.tar.gz" \
    bot/data/*.json \
    .env

echo "✅ Backup создан: $BACKUP_DIR/disrupt-data-$DATE.tar.gz"

# Удаление старых backup (старше 30 дней)
find "$BACKUP_DIR" -name "disrupt-data-*.tar.gz" -mtime +30 -delete
```

### Автоматический backup (cron)

```bash
# Создание скрипта backup
nano /home/user/Disrupt/backup.sh
# Вставить содержимое выше

# Сделать исполняемым
chmod +x /home/user/Disrupt/backup.sh

# Добавить в cron (ежедневно в 3:00)
crontab -e
# Добавить строку:
0 3 * * * /home/user/Disrupt/backup.sh
```

### Восстановление из backup

```bash
# Остановить бота
docker-compose down

# Восстановить данные
tar -xzf /home/user/backups/disrupt-data-20240119_030000.tar.gz

# Запустить бота
docker-compose up -d
```

## Мониторинг

### Настройка systemd service (автозапуск)

```bash
# Создать systemd unit
sudo nano /etc/systemd/system/disrupt-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=Disrupt Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/Disrupt
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активация:

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable disrupt-bot

# Запуск
sudo systemctl start disrupt-bot

# Проверка статуса
sudo systemctl status disrupt-bot
```

### Мониторинг ресурсов

```bash
# Использование CPU и RAM
docker stats --no-stream

# Размер логов
du -sh /var/lib/docker/containers/*/
```

## Безопасность

### Настройка firewall

```bash
# Установка UFW
sudo apt install -y ufw

# Разрешить SSH
sudo ufw allow 22/tcp

# Включить firewall
sudo ufw enable

# Проверить статус
sudo ufw status
```

### Регулярные обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose pull
docker-compose up -d
```

## Решение проблем

### Бот не запускается

```bash
# Проверка логов
docker-compose logs --tail=100

# Проверка .env файла
cat .env | grep -v "^#"

# Проверка портов
docker-compose ps
```

### Ошибки GigaChat

```bash
# Проверка credentials
echo $GIGACHAT_CREDENTIALS

# Попробовать с отключенным SSL
# В .env установить:
GIGACHAT_VERIFY_SSL=false
```

### Нехватка памяти

```bash
# Добавить swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Сделать постоянным
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Очистка Docker

```bash
# Удаление неиспользуемых образов
docker system prune -a

# Удаление всех остановленных контейнеров
docker container prune

# Очистка логов
sudo sh -c "truncate -s 0 /var/lib/docker/containers/**/*-json.log"
```

## Полезные команды

```bash
# Вход в контейнер
docker-compose exec bot bash

# Проверка переменных окружения
docker-compose exec bot env

# Рестарт без пересборки
docker-compose restart

# Просмотр всех контейнеров
docker ps -a

# Использование диска
df -h
```

## Контакты поддержки

При возникновении проблем обращайтесь к документации проекта или разработчикам.
