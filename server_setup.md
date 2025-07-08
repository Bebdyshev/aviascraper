# Настройка сервера для работы с Chrome/Selenium

## Проблема
На удаленном сервере может возникать ошибка при попытке запуска Selenium с Chrome браузером для получения кук Aviasales.

## Возможные причины
1. Chrome/Chromium не установлен
2. Отсутствуют зависимости для headless браузера
3. Проблемы с правами доступа
4. Недостаточно памяти

## Решение для Ubuntu/Debian серверов

### 1. Установка Chrome
```bash
# Обновляем систему
sudo apt update

# Устанавливаем необходимые пакеты
sudo apt install -y wget gnupg

# Добавляем ключ Google
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Добавляем репозиторий Chrome
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Обновляем и устанавливаем Chrome
sudo apt update
sudo apt install -y google-chrome-stable
```

### 2. Установка зависимостей для headless режима
```bash
sudo apt install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xvfb
```

### 3. Проверка установки
```bash
# Проверяем что Chrome установлен
google-chrome --version

# Тестируем headless режим
google-chrome --headless --disable-gpu --dump-dom https://www.google.com > /dev/null
```

## Решение для CentOS/RHEL

### 1. Установка Chrome
```bash
# Создаем репозиторий
sudo tee /etc/yum.repos.d/google-chrome.repo <<EOF
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

# Устанавливаем Chrome
sudo yum install -y google-chrome-stable
```

### 2. Установка зависимостей
```bash
sudo yum install -y \
    liberation-fonts \
    alsa-lib \
    atk \
    gtk3 \
    libX11 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrandr \
    libXrender \
    libXss \
    libXtst \
    nss \
    xvfb-run
```

## Альтернативные решения

### 1. Использование Docker
```dockerfile
FROM python:3.9-slim

# Установка Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Копируем приложение
COPY . /app
WORKDIR /app

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Запускаем приложение
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Работа без браузера (текущая реализация)
Приложение теперь имеет fallback механизм:
- Сначала пытается использовать кэшированные куки
- При ошибке 403 пытается получить свежие куки через браузер
- Если браузер недоступен, использует fallback куки
- В крайнем случае работает без кук

## Отладка проблем

### Проверка логов
```bash
# Запускаем приложение с подробными логами
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Тестирование Chrome
```bash
# Тестируем Chrome напрямую
google-chrome --headless --no-sandbox --disable-dev-shm-usage --disable-gpu --dump-dom https://www.aviasales.kz
```

### Проверка памяти
```bash
# Проверяем доступную память
free -h

# Chrome может требовать до 512MB RAM в headless режиме
```

## Рекомендации для продакшена

1. **Используйте Docker** - более предсказуемое окружение
2. **Кэшируйте куки** - минимизируйте запуски браузера
3. **Мониторьте память** - Chrome может потреблять много ресурсов
4. **Backup plan** - всегда имейте fallback без браузера 