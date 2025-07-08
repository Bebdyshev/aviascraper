#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы API Aviasales без кук
"""

import requests
import json
import uuid

START_URL = "https://tickets-api.aviasales.com/search/v2/start"

# Базовые заголовки без кук
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.aviasales.kz",
    "Referer": "https://www.aviasales.kz/",
    "Accept-Language": "ru-RU,en-US;q=0.8,ru;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "x-client-type": "web",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Priority": "u=4",
    "TE": "trailers"
}

def test_start_search():
    """Тестирует начальный поиск без кук"""
    
    # Простой тестовый поиск: Нур-Султан -> Алматы
    payload = {
        "search_params": {
            "directions": [
                {
                    "origin": "NQZ",
                    "destination": "ALA", 
                    "date": "2025-02-15",
                    "is_origin_airport": False,
                    "is_destination_airport": False,
                },
                {
                    "origin": "ALA",
                    "destination": "NQZ",
                    "date": "2025-02-20",
                    "is_origin_airport": False,
                    "is_destination_airport": False,
                }
            ],
            "passengers": {"adults": 1, "children": 0, "infants": 0},
            "trip_class": "Y",
        },
        "client_features": {
            "direct_flights": True,
            "brand_ticket": False,
            "top_filters": True,
            "badges": False,
            "tour_tickets": True,
            "assisted": True,
        },
        "market_code": "kz",
        "marker": "direct",
        "citizenship": "KZ",
        "currency_code": "kzt",
        "languages": {"ru": 1, "en": 2},
        "experiment_groups": {"usc-exp-showSupportLinkNavbar": "enabled"},
        "debug": {"override_experiment_groups": {}},
        "brand": "AS",
    }

    print("=== Тест 1: Поиск без кук ===")
    print(f"URL: {START_URL}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print(f"Headers: {json.dumps(HEADERS, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(START_URL, headers=HEADERS, json=payload, timeout=15)
        print(f"\nСтатус ответа: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Успешный ответ:")
            print(f"  search_id: {data.get('search_id')}")
            print(f"  results_url: {data.get('results_url')}")
            print(f"  search_timestamp: {data.get('search_timestamp')}")
            return True
        else:
            print(f"Ошибка {response.status_code}:")
            print(f"  Текст ответа: {response.text}")
            return False
            
    except Exception as e:
        print(f"Исключение: {type(e).__name__}: {str(e)}")
        return False

def test_with_minimal_cookies():
    """Тестирует поиск с минимальными куками"""
    
    print("\n=== Тест 2: Поиск с минимальными куками ===")
    
    headers_with_cookies = HEADERS.copy()
    headers_with_cookies["x-origin-cookie"] = "currency=KZT; marker=direct"
    
    payload = {
        "search_params": {
            "directions": [
                {
                    "origin": "NQZ",
                    "destination": "ALA", 
                    "date": "2025-02-15",
                    "is_origin_airport": False,
                    "is_destination_airport": False,
                }
            ],
            "passengers": {"adults": 1, "children": 0, "infants": 0},
            "trip_class": "Y",
        },
        "market_code": "kz",
        "marker": "direct",
        "currency_code": "kzt",
        "brand": "AS",
    }

    try:
        response = requests.post(START_URL, headers=headers_with_cookies, json=payload, timeout=15)
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Успешный ответ с минимальными куками:")
            print(f"  search_id: {data.get('search_id')}")
            return True
        else:
            print(f"Ошибка {response.status_code} с куками:")
            print(f"  Текст ответа: {response.text}")
            return False
            
    except Exception as e:
        print(f"Исключение с куками: {type(e).__name__}: {str(e)}")
        return False

def test_different_headers():
    """Тестирует различные комбинации заголовков"""
    
    print("\n=== Тест 3: Различные заголовки ===")
    
    # Минимальные заголовки
    minimal_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = {
        "search_params": {
            "directions": [{"origin": "MOW", "destination": "LED", "date": "2025-02-15"}],
            "passengers": {"adults": 1},
            "trip_class": "Y",
        },
        "market_code": "ru",
        "currency_code": "rub",
        "brand": "AS",
    }

    try:
        response = requests.post(START_URL, headers=minimal_headers, json=payload, timeout=15)
        print(f"Статус с минимальными заголовками: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  Ошибка: {response.text}")
        else:
            print(f"  Успех с минимальными заголовками!")
            
    except Exception as e:
        print(f"Исключение с минимальными заголовками: {e}")

if __name__ == "__main__":
    print("Тестирование API Aviasales без браузера")
    print("=" * 50)
    
    # Запускаем тесты
    test1_ok = test_start_search()
    test2_ok = test_with_minimal_cookies()
    test_different_headers()
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ:")
    print(f"  Тест без кук: {'✓ ПРОШЕЛ' if test1_ok else '✗ НЕ ПРОШЕЛ'}")
    print(f"  Тест с куками: {'✓ ПРОШЕЛ' if test2_ok else '✗ НЕ ПРОШЕЛ'}")
    
    if not test1_ok and not test2_ok:
        print("\nВОЗМОЖНЫЕ РЕШЕНИЯ:")
        print("1. Проверьте интернет соединение")
        print("2. Попробуйте другой User-Agent")
        print("3. Используйте VPN если есть блокировка по IP")
        print("4. Добавьте x-aws-waf-token в заголовки")
    elif test1_ok:
        print("\n✓ API работает без кук! Можно убрать зависимость от браузера.") 