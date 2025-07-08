import requests
import time
import uuid
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

COOKIES_FILE = "aviasales_cookies.json"
START_URL = "https://tickets-api.aviasales.com/search/v2/start"
RESULTS_URL = "https://tickets-api.eu-central-1.aviasales.com/search/v3.2/results"

# Basic browser-like headers to reduce chance of 403 from CloudFront
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.aviasales.kz",
    "Referer": "https://www.aviasales.kz/",
    "Accept-Language": "ru-RU,en-US;q=0.8,ru;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "x-client-type": "web",
    "x-aws-waf-token": "a097d6e8-b953-4b4b-8cce-127af45b1048:BQoAfW5++YJGAQAA:VY+FCaJ4N9XAcszXACeEk2H3Dzr+Eq69EnrKQWcveW/hPO/K0gOWlt+lDOvHga3ofG2nAQ2yWyL5hQ4hwwMSZtHcDHQjxOw3ddTFSDdHVCBIqIU58kdYXQBjYsN295oUfxCTr4Jy7jYxtbEuSvSOghx7aSbO4LzY1BnmId8HV22ZItE4iHp/p8vhAPEJdyvWJFYmlVPwN1gow3Dy8WRs0bHASrhWLtC0VcG1XgX/T2tqkOP26LEi7rYHS9BBgF4iIG3NfA==",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Priority": "u=4",
    "TE": "trailers"
}

# --- Pydantic Models for FastAPI ---
class Direction(BaseModel):
    origin: str
    destination: str
    date: str

class Passengers(BaseModel):
    adults: int
    children: int = 0
    infants: int = 0

class SearchRequest(BaseModel):
    directions: List[Direction]
    passengers: Passengers
    trip_class: str = "Y"
    market: str = "kz"
    currency: str = "kzt"

app = FastAPI()

def build_aviasales_token(ticket: dict) -> str:
    """
    Формирует строку для ?t=... по данным билета Aviasales.
    Ожидает структуру ticket, аналогичную summary (см. build_summary).
    """
    def seg_to_str(leg):
        # Код авиакомпании (2-3 буквы)
        airline = leg.get("airline_id", "")[:2]
        # Время вылета/прилета (unix, 10 цифр)
        dep = str(leg.get("departure_unix_timestamp", 0)).zfill(10)
        arr = str(leg.get("arrival_unix_timestamp", 0)).zfill(10)
        # Длительность (в минутах, 8 цифр)
        duration = int((leg.get("arrival_unix_timestamp", 0) or 0) - (leg.get("departure_unix_timestamp", 0) or 0)) // 60
        duration_str = str(duration).zfill(8)
        # Коды аэропортов (3*3=9 символов)
        oa = leg.get("origin", "XXX")[:3]
        ma = leg.get("middle", "")[:3]  # middle может отсутствовать
        da = leg.get("destination", "XXX")[:3]
        # Если middle отсутствует, берем только oa+da
        if ma:
            airports = f"{oa}{ma}{da}"
        else:
            airports = f"{oa}{da}"
        return f"{airline}{dep}{arr}{duration_str}{airports}"

    # Собираем все сегменты (туда + обратно)
    segs = []
    for leg in ticket.get("flights_to", []):
        segs.append(seg_to_str(leg))
    for leg in ticket.get("flights_return", []):
        segs.append(seg_to_str(leg))
    part_a = "".join(segs)

    # Подпись (signature/hash)
    signature = ticket.get("id")

    # Цена (в копейках/центах/рублях*100)
    price_val = ticket.get("unified_price", 0)
    try:
        price_int = int(round(float(price_val) * 100))
    except Exception:
        price_int = 0
    part_c = str(price_int)

    return f"{part_a}_{signature}_{part_c}"

def build_aviasales_token_v2(ticket: dict) -> str:
    """
    Формирует строку для ?t=... по новому формату:
    {carrier_id}{unix_departure}{unix_arrival}{duration6}{airports_to}{unix_departure_return}{unix_arrival_return}{duration6_return}{airports_return}_{ticket_id}_{price_in_rub}
    carrier_id — последний код авиакомпании из всего маршрута
    Для unix_departure/unix_arrival брать из signature первого/последнего сегмента (первое/второе число).
    """
    def get_signature_times(leg):
        sig = leg.get("signature")
        if sig and ":" in sig:
            parts = sig.split(":")
            if len(parts) >= 2:
                try:
                    return int(parts[0]), int(parts[1])
                except Exception:
                    pass
        # fallback
        return (
            int(leg.get("departure_unix_timestamp", 0)),
            int(leg.get("arrival_unix_timestamp", 0)),
        )

    flights_to = ticket.get("flights_to", [])
    flights_return = ticket.get("flights_return", [])
    all_legs = flights_to + flights_return
    if not flights_to or not flights_return or not all_legs:
        return ""
    # carrier_id — последний код авиакомпании из всего маршрута
    carrier_id = all_legs[-1].get("airline_id", "XX")
    # Туда
    dep_to, _ = get_signature_times(flights_to[0])
    _, arr_to = get_signature_times(flights_to[-1])
    duration_to = (arr_to - dep_to) // 60
    duration_to_str = str(duration_to).zfill(6)
    airports_to = "".join(leg.get("origin", "XXX") for leg in flights_to) + flights_to[-1].get("destination", "XXX")
    # Обратно
    dep_ret, _ = get_signature_times(flights_return[0])
    _, arr_ret = get_signature_times(flights_return[-1])
    duration_ret = (arr_ret - dep_ret) // 60
    duration_ret_str = str(duration_ret).zfill(6)
    airports_ret = "".join(leg.get("origin", "XXX") for leg in flights_return) + flights_return[-1].get("destination", "XXX")
    # ticket_id
    ticket_id = ticket.get("id", "noticket")
    # price in rub (без копеек, округлить вниз)
    price_val = ticket.get("price", {}).get("value", 0)
    try:
        price_rub = int(float(price_val))
    except Exception:
        price_rub = 0
    token = f"{carrier_id}{dep_to}{arr_to}{duration_to_str}{airports_to}{dep_ret}{arr_ret}{duration_ret_str}{airports_ret}_{ticket_id}_{price_rub}"
    return token

def start_search(payload: dict, headers: dict) -> tuple[str, str, str]:
    """Initiate Aviasales search and return (search_id, results_host)."""
    print("Headers:", headers)
    resp = requests.post(START_URL, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    search_id = data.get("search_id")
    timestamp = data.get("search_timestamp")
    assert search_id, "search_id not found in start response"

    results_host = data.get("results_url", "tickets-api.eu-central-1.aviasales.com")
    return search_id, results_host, timestamp


def poll_results(search_id: str, results_host: str, limit: int = 100, max_attempts: int = 10, delay: int = 1) -> dict:
    """Poll the results endpoint until tickets appear or max attempts reached. Делает минимум 3 попытки polling."""
    last_ts = 0
    body_base = {
        "limit": limit,
        "price_per_person": False,
        "search_by_airport": False,
        "search_id": search_id,
    }

    data = None
    for attempt in range(1, max_attempts + 1):
        body = {**body_base, "last_update_timestamp": last_ts}
        headers = HEADERS.copy()
        headers["x-request-id"] = str(uuid.uuid4())
        results_url = f"https://{results_host}/search/v3.2/results"
        print(f"Polling attempt {attempt}/{max_attempts} (ts={last_ts})…")
        try:
            resp = requests.post(results_url, headers=headers, json=body, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Print minimal progress info
            if attempt == 1 or attempt % 3 == 0:
                if isinstance(data, dict):
                    print("Keys:", list(data.keys())[:10])
                else:
                    print(f"Received list with {len(data)} items")
            # Update timestamp if dict contains it
            if isinstance(data, dict):
                last_ts = data.get("last_update_timestamp", last_ts)

            if len(data[0].get('tickets')) >= 100:
                return data
            
            print(len(data[0].get('tickets')))

            time.sleep(1)

        except Exception as e:
            print(f"Request error: {e}")
            raise

    raise TimeoutError("No ticket data returned within polling attempts")


def get_x_origin_cookie(force_refresh: bool = False) -> str:
    """
    Gets cookies, from cache if available, or via Selenium if forced/needed.
    Set force_refresh=True to ignore cache and get new cookies.
    """
    if not force_refresh and os.path.exists(COOKIES_FILE):
        print("Loading cookies from cache...")
        try:
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
            # Basic validation to ensure file is not empty/corrupt
            if cookies and isinstance(cookies, list):
                return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Could not read cookie file, fetching new ones. Error: {e}")
            # Fall through to fetch new cookies

    print("Fetching fresh cookies via Selenium (this might take a moment)...")
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")  # Часто нужно для серверов
    options.add_argument("--disable-dev-shm-usage")  # Помогает с памятью
    options.add_argument("--disable-gpu")  # Отключает GPU на серверах
    options.add_argument("--remote-debugging-port=9222")  # Для отладки
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0")
    
    driver = None
    try:
        print("Installing ChromeDriver...")
        service = ChromeService(ChromeDriverManager().install())
        print("Starting Chrome browser...")
        driver = webdriver.Chrome(service=service, options=options)
        
        print("Navigating to Aviasales...")
        # Go to a search page to ensure all necessary cookies are set
        driver.get("https://www.aviasales.kz/search/NQZ0108AKX15081")
        # A small wait can help with cookies set by JS after load
        time.sleep(3)

        print("Extracting cookies...")
        cookies = driver.get_cookies()
        
        print(f"Found {len(cookies)} cookies")
        if not cookies:
            raise Exception("No cookies found")
            
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        print("Successfully fetched and cached new cookies.")

        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        
    except Exception as e:
        error_msg = f"Selenium failed: {type(e).__name__}: {str(e)}"
        print(f"ERROR: {error_msg}")
        
        # Fallback: попробуем использовать статические куки или вернуть пустую строку
        print("Trying fallback approach...")
        fallback_cookies = get_fallback_cookies()
        if fallback_cookies:
            print("Using fallback cookies")
            return fallback_cookies
        else:
            print("No fallback cookies available")
            # Возвращаем пустую строку вместо краха приложения
            return ""
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing driver: {e}")


def get_fallback_cookies() -> str:
    """
    Возвращает заранее подготовленные куки как fallback, 
    если Selenium не работает на сервере
    """
    # Можно вручную добавить некоторые базовые куки
    # Это не идеальное решение, но лучше чем полный крах
    fallback = "currency=KZT; marker=direct; auid=fallback"
    return fallback

def build_summary(api_response, start_payload):
    # If response is list of chunks, find the one with chunk_id == "results"
    if isinstance(api_response, list):
        for chunk in api_response:
            if isinstance(chunk, dict) and chunk.get("chunk_id") == "results":
                api_response = chunk
                break

    if not isinstance(api_response, dict):
        return []

    summary_tickets = []
    flight_legs = api_response.get("flight_legs", [])
    if not isinstance(flight_legs, list):
        return summary_tickets

    places = api_response.get("places", {})
    cities = places.get("cities", {})
    countries = places.get("countries", {})

    # Build airport->city name mapping
    airports_dict = places.get("airports", {})
    airport_to_city_ru = {}
    airport_to_city_en = {}
    for a_code, a_info in airports_dict.items():
        city_code = a_info.get("city_code")
        if city_code and city_code in cities:
            city_name_ru = cities[city_code].get("name", {}).get("ru", {}).get("default")
            city_name_en = cities[city_code].get("name", {}).get("en", {}).get("default")
            if city_name_ru:
                airport_to_city_ru[a_code] = city_name_ru
            if city_name_en:
                airport_to_city_en[a_code] = city_name_en

    def zero_pad(val, width=8):
        return str(val).zfill(width)

    def get_signature_times(leg):
        sig = leg.get("signature")
        if sig and ":" in sig:
            parts = sig.split(":")
            if len(parts) >= 2:
                try:
                    return int(parts[0]), int(parts[1])
                except Exception:
                    pass
        # fallback
        return (
            int(leg.get("departure_unix_timestamp", 0)),
            int(leg.get("arrival_unix_timestamp", 0)),
        )

    for ticket in api_response.get("tickets", []):
        item = {
            "id": ticket.get("id"),
            "price": ticket.get("proposals", [{}])[0].get("price", {}),
            "flights_to": [],
            "flights_return": []
        }
        # Новые поля summary
        item["ticket_id"] = ticket.get("id")
        price_val = item["price"].get("value", 0)
        item["unified_price"] = int(round(float(price_val) * 100))
        flights_to_unix_departure = []
        flights_to_unix_arrival = []
        flights_to_airline_id = []
        flights_to_airports = []
        duration_to = 0
        flights_return_unix_departure = []
        flights_return_unix_arrival = []
        flights_return_airline_id = []
        flights_return_airports = []
        duration_return = 0
        segments = ticket.get("segments", [])
        for seg_idx, segment in enumerate(segments):
            for idx in segment.get("flights", []):
                if 0 <= idx < len(flight_legs):
                    leg = dict(flight_legs[idx])  # copy
                    oa = leg.get("origin")
                    da = leg.get("destination")
                    leg["origin_city_ru"] = airport_to_city_ru.get(oa, oa)
                    leg["destination_city_ru"] = airport_to_city_ru.get(da, da)
                    leg["origin_city_en"] = airport_to_city_en.get(oa, oa)
                    leg["destination_city_en"] = airport_to_city_en.get(da, da)
                    carrier_code = leg.get("operating_carrier_designator", {}).get("carrier", "")
                    leg["airline_id"] = carrier_code
                    unix_dep = leg.get("departure_unix_timestamp")
                    unix_arr = leg.get("arrival_unix_timestamp")
                    airports_ids = (oa, da)
                    # duration по signature
                    sig_dep, sig_arr = get_signature_times(leg)
                    duration = (sig_arr - sig_dep) // 60 if sig_dep and sig_arr else 0
                    if seg_idx == 0:
                        item["flights_to"].append(leg)
                        flights_to_unix_departure.append(unix_dep)
                        flights_to_unix_arrival.append(unix_arr)
                        flights_to_airline_id.append(carrier_code)
                        flights_to_airports.append(airports_ids)
                        duration_to += duration
                    else:
                        item["flights_return"].append(leg)
                        flights_return_unix_departure.append(unix_dep)
                        flights_return_unix_arrival.append(unix_arr)
                        flights_return_airline_id.append(carrier_code)
                        flights_return_airports.append(airports_ids)
                        duration_return += duration
        # Determine route names based on first outbound and last return
        first_leg = item["flights_to"][0] if item["flights_to"] else None
        last_leg = item["flights_return"][-1] if item["flights_return"] else None
        if first_leg and last_leg:
            item["route_ru"] = f"{first_leg['origin_city_ru']} → {last_leg['destination_city_ru']}"
            item["route_en"] = f"{first_leg['origin_city_en']} → {last_leg['destination_city_en']}"
        # Новые поля
        item["flights_to_unix_departure"] = flights_to_unix_departure
        item["flights_to_unix_arrival"] = flights_to_unix_arrival
        item["flights_to_airline_id"] = flights_to_airline_id
        item["flights_to_airports"] = flights_to_airports
        item["duration_to"] = zero_pad(duration_to, 8)
        item["flights_return_unix_departure"] = flights_return_unix_departure
        item["flights_return_unix_arrival"] = flights_return_unix_arrival
        item["flights_return_airline_id"] = flights_return_airline_id
        item["flights_return_airports"] = flights_return_airports
        item["duration_return"] = zero_pad(duration_return, 8)
        summary_tickets.append(item)

        # Формируем ссылку Aviasales
        def get_url():
            # origin, dest, dates из start_payload или legs
            try:
                origin = start_payload["search_params"]["directions"][0]["origin"]
                dest = start_payload["search_params"]["directions"][0]["destination"]
                # Преобразуем YYYY-MM-DD -> DDMM
                date_departure_full = start_payload["search_params"]["directions"][0]["date"]
                date_return_full = start_payload["search_params"]["directions"][1]["date"]
                date_departure = date_departure_full[8:10] + date_departure_full[5:7]
                date_return = date_return_full[8:10] + date_return_full[5:7]
                passengers = f"1"
            except Exception:
                origin = dest = date_departure = date_return = passengers = ""
            token = build_aviasales_token_v2(item)
            return f"https://www.aviasales.kz/search/{origin}{date_departure}{dest}{date_return}{passengers}?t={token}"
        item["aviasales_url"] = get_url()

    # Determine cheapest ticket
    cheapest = None
    for t in summary_tickets:
        price_val = t.get("price", {}).get("value", float("inf"))
        if cheapest is None or price_val < cheapest.get("price", {}).get("value", float("inf")):
            cheapest = t

    return {
        "cheapest_ticket": cheapest,
        "tickets": summary_tickets,
        "cities": cities,
        "city_names_ru": list(city_name_ru for city_name_ru in airport_to_city_ru.values()),
        "city_names_en": list(city_name_en for city_name_en in airport_to_city_en.values()),
        "countries": countries,
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/search")
async def search_flights(request_data: SearchRequest):
    start_payload = {
        "search_params": {
            "directions": [
                {
                    "origin": d.origin,
                    "destination": d.destination,
                    "date": d.date,
                    "is_origin_airport": False,
                    "is_destination_airport": False,
                }
                for d in request_data.directions
            ],
            "passengers": request_data.passengers.dict(),
            "trip_class": request_data.trip_class,
        },
        "client_features": {
            "direct_flights": True,
            "brand_ticket": False,
            "top_filters": True,
            "badges": False,
            "tour_tickets": True,
            "assisted": True,
        },
        "market_code": request_data.market,
        "marker": "direct",
        "citizenship": "KZ",
        "currency_code": request_data.currency,
        "languages": {"ru": 1, "en": 2},
        "experiment_groups": {"usc-exp-showSupportLinkNavbar": "enabled"},
        "debug": {"override_experiment_groups": {}},
        "brand": "AS",
    }

    current_headers = HEADERS.copy()
    
    try:
        print("Getting cookies...")
        x_origin_cookie = get_x_origin_cookie()
        if x_origin_cookie:
            current_headers["x-origin-cookie"] = x_origin_cookie
            print(f"Using cookies: {x_origin_cookie[:100]}..." if len(x_origin_cookie) > 100 else f"Using cookies: {x_origin_cookie}")
        else:
            print("No cookies available, trying without x-origin-cookie header")

        print("Starting search with current cookies...")
        sid, host, timestamp = start_search(start_payload, current_headers)
        print("search_id:", sid)
        res = poll_results(sid, host)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"Request failed with {e.response.status_code}. Trying to refresh cookies...")
            
            try:
                x_origin_cookie = get_x_origin_cookie(force_refresh=True)
                if x_origin_cookie and x_origin_cookie != "currency=KZT; marker=direct; auid=fallback":
                    current_headers["x-origin-cookie"] = x_origin_cookie
                    print("Retrying search with fresh cookies...")
                    sid, host, timestamp = start_search(start_payload, current_headers)
                    print("search_id:", sid)
                    res = poll_results(sid, host)
                else:
                    # Если даже fallback куки не помогли, попробуем без них
                    print("Fresh cookies failed, trying without x-origin-cookie header...")
                    if "x-origin-cookie" in current_headers:
                        del current_headers["x-origin-cookie"]
                    sid, host, timestamp = start_search(start_payload, current_headers)
                    print("search_id:", sid)
                    res = poll_results(sid, host)
                    
            except Exception as refresh_error:
                print(f"Cookie refresh failed: {refresh_error}")
                # Последняя попытка без кук
                print("Final attempt without cookies...")
                if "x-origin-cookie" in current_headers:
                    del current_headers["x-origin-cookie"]
                try:
                    sid, host, timestamp = start_search(start_payload, current_headers)
                    print("search_id:", sid)
                    res = poll_results(sid, host)
                except Exception as final_error:
                    raise HTTPException(
                        status_code=503, 
                        detail=f"All attempts failed. Original error: {e.response.status_code}, Cookie refresh error: {refresh_error}, Final error: {final_error}"
                    )
        else:
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e}")
            
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=f"Polling timed out: {e}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    summary_data = build_summary(res, start_payload)

    # Optionally save results to files
    # with open("aviasales_raw.json", "w", encoding="utf-8") as f:
    #     json.dump(res, f, ensure_ascii=False, indent=2)
    # summary_file = f"aviasales_summary.json"
    # with open(summary_file, "w", encoding="utf-8") as f:
    #     json.dump(summary_data, f, ensure_ascii=False, indent=2)

    return summary_data
 