════════════════════════════════════════════════════════════════
  ИНСТРУКЦИЯ ПО РАЗВЕРТЫВАНИЮ БОТА "ДИЗРАПТ" НА UBUNTU СЕРВЕРЕ
════════════════════════════════════════════════════════════════

📋 СОДЕРЖАНИЕ:
1. Подготовка сервера
2. Установка Docker и Docker Compose
3. Загрузка проекта на сервер
4. Настройка переменных окружения
5. Запуск бота
6. Управление ботом
7. Резервное копирование
8. Решение проблем

════════════════════════════════════════════════════════════════
1. ПОДГОТОВКА СЕРВЕРА
════════════════════════════════════════════════════════════════

Минимальные требования:
- Ubuntu 20.04 или выше
- 1 GB RAM (рекомендуется 2 GB)
- 10 GB свободного места на диске
- Доступ к интернету

Подключитесь к серверу по SSH:
ssh user@your-server-ip


════════════════════════════════════════════════════════════════
2. УСТАНОВКА DOCKER И DOCKER COMPOSE
════════════════════════════════════════════════════════════════

Выполните следующие команды на сервере:

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common git

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

# ВАЖНО: Перелогиньтесь для применения изменений
exit
# Подключитесь снова
ssh user@your-server-ip

# Проверка установки
docker --version
docker-compose --version


════════════════════════════════════════════════════════════════
3. ЗАГРУЗКА ПРОЕКТА НА СЕРВЕР
════════════════════════════════════════════════════════════════

ВАРИАНТ A: Через архив (если проект в архиве)
--------------------------------------------------------------

На локальной машине создайте архив:
cd "Disrupt"
tar -czf disrupt-bot.tar.gz --exclude='venv' --exclude='.git' --exclude='__pycache__' --exclude='bot/data/*.json' .

Передайте на сервер:
scp disrupt-bot.tar.gz user@your-server-ip:/home/user/

На сервере распакуйте:
cd /home/user
mkdir -p Disrupt
tar -xzf disrupt-bot.tar.gz -C Disrupt
cd Disrupt

ВАРИАНТ B: Через Git (если есть репозиторий)
--------------------------------------------------------------

git clone <url-репозитория>
cd Disrupt


════════════════════════════════════════════════════════════════
4. НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
════════════════════════════════════════════════════════════════

Создайте .env файл на основе примера:
cp .env.example .env
nano .env

Заполните следующие параметры:

BOT_TOKEN=your_bot_token_here
  └─ Получить у @BotFather в Telegram
  └─ Отправьте /newbot и следуйте инструкциям
  └─ Скопируйте токен вида: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

ADMINS=[123456789,987654321]
  └─ Ваш Telegram user_id (узнать у @userinfobot)
  └─ Можно указать несколько через запятую
  └─ Формат: JSON массив чисел

GIGACHAT_CREDENTIALS=your_gigachat_credentials
  └─ Получить на https://developers.sber.ru/portal/products/gigachat
  └─ Зарегистрируйтесь и создайте API ключ
  └─ Скопируйте Base64 credentials

GIGACHAT_SCOPE=GIGACHAT_API_PERS
  └─ Оставьте по умолчанию

GIGACHAT_VERIFY_SSL=false
  └─ Оставьте false для разработки

Сохраните файл:
Ctrl+O (сохранить)
Enter (подтвердить)
Ctrl+X (выйти)


════════════════════════════════════════════════════════════════
5. ЗАПУСК БОТА
════════════════════════════════════════════════════════════════

СПОСОБ 1: Автоматический запуск (рекомендуется)
--------------------------------------------------------------

./deploy.sh

Скрипт автоматически:
✓ Инициализирует базу данных
✓ Остановит старые контейнеры
✓ Соберет Docker образ
✓ Запустит бота
✓ Покажет статус

СПОСОБ 2: Ручной запуск
--------------------------------------------------------------

# Инициализация базы данных
./init_data.sh

# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

СПОСОБ 3: Production запуск с ограничениями ресурсов
--------------------------------------------------------------

docker-compose -f docker-compose.prod.yml up -d --build


════════════════════════════════════════════════════════════════
6. УПРАВЛЕНИЕ БОТОМ
════════════════════════════════════════════════════════════════

Просмотр логов в реальном времени:
docker-compose logs -f

Просмотр последних 100 строк логов:
docker-compose logs --tail=100

Остановка бота:
docker-compose down

Перезапуск бота:
docker-compose restart

Проверка статуса:
docker-compose ps

Просмотр использования ресурсов:
docker stats

Вход в контейнер для отладки:
docker-compose exec bot bash


════════════════════════════════════════════════════════════════
7. РЕЗЕРВНОЕ КОПИРОВАНИЕ
════════════════════════════════════════════════════════════════

Создание backup базы данных:
--------------------------------------------------------------

tar -czf backup-$(date +%Y%m%d_%H%M%S).tar.gz bot/data/*.json .env

Автоматический backup (добавить в cron):
--------------------------------------------------------------

# Создать скрипт backup
nano /home/user/Disrupt/backup.sh

Содержимое:
────────────────────────────────────────────────
#!/bin/bash
BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
cd /home/user/Disrupt
tar -czf "$BACKUP_DIR/disrupt-data-$DATE.tar.gz" bot/data/*.json .env
find "$BACKUP_DIR" -name "disrupt-data-*.tar.gz" -mtime +30 -delete
────────────────────────────────────────────────

Сделать исполняемым:
chmod +x /home/user/Disrupt/backup.sh

Добавить в cron (ежедневно в 3:00):
crontab -e
# Добавить строку:
0 3 * * * /home/user/Disrupt/backup.sh

Восстановление из backup:
--------------------------------------------------------------

docker-compose down
tar -xzf /home/user/backups/disrupt-data-20240119_030000.tar.gz
docker-compose up -d


════════════════════════════════════════════════════════════════
8. РЕШЕНИЕ ПРОБЛЕМ
════════════════════════════════════════════════════════════════

Проблема: Бот не запускается
────────────────────────────────────────────────
Решение:
1. Проверьте логи: docker-compose logs --tail=100
2. Проверьте .env файл: cat .env
3. Убедитесь, что BOT_TOKEN правильный
4. Проверьте, что контейнер запущен: docker-compose ps

Проблема: Ошибка "Could not find a version that satisfies"
────────────────────────────────────────────────
Решение:
1. Пересоберите образ: docker-compose build --no-cache
2. Обновите pip в Dockerfile (если нужно)

Проблема: GigaChat не отвечает
────────────────────────────────────────────────
Решение:
1. Проверьте GIGACHAT_CREDENTIALS в .env
2. Установите GIGACHAT_VERIFY_SSL=false
3. Проверьте доступ к API: curl https://gigachat.devices.sberbank.ru/

Проблема: Нехватка памяти
────────────────────────────────────────────────
Решение:
# Добавить swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

Проблема: Контейнер постоянно перезапускается
────────────────────────────────────────────────
Решение:
1. Проверьте логи: docker-compose logs -f
2. Убедитесь, что все переменные в .env заполнены
3. Проверьте права на директорию bot/data/: ls -la bot/data/

Проблема: Потеря данных после перезапуска
────────────────────────────────────────────────
Решение:
1. Убедитесь, что volume смонтирован в docker-compose.yml
2. Проверьте: docker-compose config | grep volumes
3. Данные должны быть в ./bot/data на хосте

Проблема: "Permission denied" при запуске скриптов
────────────────────────────────────────────────
Решение:
chmod +x deploy.sh init_data.sh


════════════════════════════════════════════════════════════════
9. АВТОЗАПУСК БОТА ЧЕРЕЗ SYSTEMD
════════════════════════════════════════════════════════════════

Создайте systemd service:
sudo nano /etc/systemd/system/disrupt-bot.service

Содержимое:
────────────────────────────────────────────────
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
────────────────────────────────────────────────

Активация:
sudo systemctl daemon-reload
sudo systemctl enable disrupt-bot
sudo systemctl start disrupt-bot
sudo systemctl status disrupt-bot


════════════════════════════════════════════════════════════════
10. ОБНОВЛЕНИЕ БОТА
════════════════════════════════════════════════════════════════

Через Git:
--------------------------------------------------------------
cd /home/user/Disrupt
docker-compose down
git pull
docker-compose up -d --build

Через архив:
--------------------------------------------------------------
cd /home/user/Disrupt
docker-compose down
# Загрузите новый архив на сервер
tar -xzf ~/disrupt-bot-new.tar.gz
docker-compose up -d --build


════════════════════════════════════════════════════════════════
11. МОНИТОРИНГ
════════════════════════════════════════════════════════════════

Просмотр использования ресурсов:
docker stats --no-stream

Проверка свободного места:
df -h

Проверка памяти:
free -h

Размер логов Docker:
du -sh /var/lib/docker/containers/*/

Очистка Docker:
docker system prune -a


════════════════════════════════════════════════════════════════
12. БЕЗОПАСНОСТЬ
════════════════════════════════════════════════════════════════

Настройка firewall:
--------------------------------------------------------------
sudo apt install -y ufw
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
sudo ufw status

Регулярные обновления:
--------------------------------------------------------------
# Еженедельно обновляйте систему
sudo apt update && sudo apt upgrade -y

# Обновляйте Docker образы
docker-compose pull
docker-compose up -d

Защита .env файла:
--------------------------------------------------------------
chmod 600 .env


════════════════════════════════════════════════════════════════
13. ПОЛЕЗНЫЕ КОМАНДЫ
════════════════════════════════════════════════════════════════

# Просмотр всех контейнеров
docker ps -a

# Просмотр образов
docker images

# Очистка неиспользуемых образов
docker image prune -a

# Очистка всего неиспользуемого
docker system prune -a --volumes

# Перезапуск без пересборки
docker-compose restart

# Остановка с удалением volumes
docker-compose down -v

# Просмотр переменных окружения в контейнере
docker-compose exec bot env

# Копирование файла из контейнера
docker cp disrupt-bot:/app/bot/data/users.json ./users-backup.json


════════════════════════════════════════════════════════════════
14. КОНТАКТЫ И ПОДДЕРЖКА
════════════════════════════════════════════════════════════════

Документация:
- README.md - основная документация
- DEPLOYMENT.md - подробная инструкция по развертыванию

Структура проекта:
- bot/ - код бота
- bot/data/ - JSON база данных
- Dockerfile - конфигурация Docker
- docker-compose.yml - оркестрация контейнеров
- .env - переменные окружения

При возникновении проблем:
1. Проверьте логи: docker-compose logs -f
2. Проверьте статус: docker-compose ps
3. Проверьте ресурсы: docker stats
4. Обратитесь к разработчикам

════════════════════════════════════════════════════════════════
УСПЕШНОГО РАЗВЕРТЫВАНИЯ! 🚀
════════════════════════════════════════════════════════════════
