# Настройка сервера для работы с Playwright

## Проблема
На удаленном сервере может возникать ошибка при попытке запуска браузера для получения кук Aviasales.

## Возможные причины
1. Playwright браузеры не установлены
2. Отсутствуют системные зависимости для headless браузера
3. Проблемы с правами доступа
4. Недостаточно памяти

## Решение для Ubuntu/Debian серверов

### 1. Установка Python зависимостей
```bash
# Устанавливаем Python зависимости
pip install -r requirements.txt
```

### 2. Установка Playwright браузеров
```bash
# Устанавливаем браузеры Playwright (автоматически загружает Chromium, Firefox, WebKit)
playwright install

# Или только Chromium (рекомендуется для серверов)
playwright install chromium

# Устанавливаем системные зависимости для браузеров
playwright install-deps
```

### 3. Проверка установки
```bash
# Проверяем что Playwright работает
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Тестируем headless браузер
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.google.com')
    print('Headless browser works!')
    browser.close()
"
```

## Решение для CentOS/RHEL

### 1. Установка зависимостей
```bash
# Устанавливаем Python зависимости
pip install -r requirements.txt

# Устанавливаем Playwright браузеры
playwright install chromium
playwright install-deps
```

### 2. Дополнительные зависимости для старых систем
```bash
sudo yum install -y \
    liberation-fonts \
    alsa-lib \
    atk \
    gtk3 \
    libdrm \
    libX11 \
    libXcomposite \
    libXdamage \
    libXext \
    libXfixes \
    libxkbcommon \
    libXrandr \
    mesa-libgbm \
    nspr \
    nss
```

## Альтернативные решения

### 1. Использование Docker
```dockerfile
FROM python:3.9-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Копируем приложение
COPY . /app
WORKDIR /app

# Устанавливаем Python зависимости
RUN pip install -r requirements.txt

# Устанавливаем Playwright браузеры
RUN playwright install chromium
RUN playwright install-deps

# Запускаем приложение
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Работа без браузера (текущая реализация)
Приложение имеет fallback механизм:
- Сначала пытается использовать кэшированные куки
- При ошибке 403 пытается получить свежие куки через Playwright
- Если браузер недоступен, использует fallback куки
- В крайнем случае работает без кук

## Преимущества Playwright над Selenium

1. **Встроенные браузеры** - не нужно устанавливать Chrome/ChromeDriver
2. **Лучшая производительность** - быстрее запуск и выполнение
3. **Стабильность** - меньше проблем с версиями драйверов
4. **Простая установка** - одна команда `playwright install`
5. **Лучшая поддержка headless** - оптимизирован для серверов

## Отладка проблем

### Проверка логов
```bash
# Запускаем приложение с подробными логами
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

### Тестирование Playwright
```bash
# Тестируем Playwright напрямую
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://www.aviasales.kz')
    print('Cookies:', len(context.cookies()))
    browser.close()
"
```

### Проверка памяти
```bash
# Проверяем доступную память
free -h

# Playwright + Chromium обычно требует ~300MB RAM в headless режиме
```

### Решение проблем с разрешениями
```bash
# Если ошибки с разрешениями
chmod +x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome

# Или переустановить браузеры
playwright uninstall --all
playwright install chromium
```

## Рекомендации для продакшена

1. **Используйте только Chromium** - `playwright install chromium` (экономит место)
2. **Docker контейнеры** - более предсказуемое окружение
3. **Кэшируйте куки** - минимизируйте запуски браузера
4. **Мониторьте память** - Playwright потребляет меньше памяти чем Selenium
5. **Регулярно обновляйте** - `playwright install chromium` для новых версий

## Устранение неполадок

### Ошибка "Browser not found"
```bash
playwright install chromium
```

### Ошибка "Missing dependencies"
```bash
playwright install-deps
```

### Ошибка "Permission denied"
```bash
# Проверить права на папку с браузерами
ls -la ~/.cache/ms-playwright/
# При необходимости исправить права
chmod -R 755 ~/.cache/ms-playwright/
```

Playwright значительно упрощает развертывание на серверах по сравнению с Selenium! 