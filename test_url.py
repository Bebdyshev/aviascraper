import requests
import json

def make_aviasales_request():
    """
    Replicates the provided cURL command to start a search on Aviasales.
    """
    url = "https://tickets-api.aviasales.com/search/v2/start"

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://www.aviasales.kz/',
        'authorization': '',
        'content-type': 'application/json',
        'x-client-type': 'web',
        "x-aws-waf-token": "a097d6e8-b953-4b4b-8cce-127af45b1048:BQoAfW5++YJGAQAA:VY+FCaJ4N9XAcszXACeEk2H3Dzr+Eq69EnrKQWcveW/hPO/K0gOWlt+lDOvHga3ofG2nAQ2yWyL5hQ4hwwMSZtHcDHQjxOw3ddTFSDdHVCBIqIU58kdYXQBjYsN295oUfxCTr4Jy7jYxtbEuSvSOghx7aSbO4LzY1BnmId8HV22ZItE4iHp/p8vhAPEJdyvWJFYmlVPwN1gow3Dy8WRs0bHASrhWLtC0VcG1XgX/T2tqkOP26LEi7rYHS9BBgF4iIG3NfA==",
        'x-origin-cookie': 'crt=744; auid=VzZXSGhEbM1jZFY0RFBmAg==; currency=USD; _gcl_au=1.1.1954226527.1749314771; uxs_uid=f546caf0-43be-11f0-ace6-41fd33ab94ec; _yoid=9a56a1d3-8068-4e7e-98fc-c237a2979928; _gcl_aw=GCL.1749372844.CjwKCAjw6ZTCBhBOEiwAqfwJd_ziNagnDlAarQEZALPYWgdtR7WUfAhVA8YugpHuo5C5tjaK9GzFJRoC03gQAvD_BwE; _gcl_gs=2.1.k1$i1749372840$u141248610; _ym_uid=1749314772913012802; _ym_d=1749581591; cookies_policy=%7B%22accepted%22%3Atrue%2C%22technical%22%3Atrue%2C%22marketing%22%3Atrue%7D; _yosid=a7a5302a-9e55-4697-b20c-296ee5cd97bc; click_meta=%7C3101998579768968352%3B238%3B1749368470766%7C3103791210048164416%3B238%3B1749582168937%7C3103804468887214976%3B238%3B1749583749515%7C3104134660394459744%3B120%3B1749623111353%7C3104138969462488960%3B120%3B1749623625042%7C3120388899097183552%3B238%3B1751560766971%7C3120909586809620064%3B238%3B1751622838566%7C3120909850505512544%3B65%3B1751622869938%7C3120915757536773728%3B65%3B1751623574050%7C3120915825778099808%3B65%3B1751623582178%7C3120915886596110208%3B65%3B1751623589423; currency=usd; crt=132; _awt=566533f36333632473e3276576327337641f169f562-49a33245d3f406c136b247636523862616d1d; _ym_isad=2; _ym_visorc=b; _ga=GA1.1.772074943.1749581591; _ga_HFKMEKWMMM=GS2.1.s1751950576$o38$g1$t1751950583$j53$l0$h0; _fbp=fb.1.1749581592210.30811988377604114; aws-waf-token=7874dc40-5cb5-4347-822c-1ce3dc95ca71:BQoAku4hgrcbAQAA:aNLl59ZLFxEOMyVtzKGsxYkcEzEFeQVN2qSEXKW2e8ldmoFwXetLTUSbo4bXbD3VF6zgOxq9IrFmDSBxnAqUmmiL0ZMFB0qgszXHKACFnpmOIdJ7CWoSkqHAlpNnEeZPxafjzKPNAjVEF08J07RsZe2eIezMWZNtN3vwevVv7RBGHlY+klO2z6YTc00hfPzCsq0VqoEI0Lg1y5Lf46J2IBDHnrK4U0OB0im7D55wpSAu6m1ggD1aNiXsGI8lShw4kZxSYg==; uncheck_hotel_cookie=true; marker=272343.Zzf55971eeeb094cbdbdbb27a-272343; _sp_ses.25b7=*; _sp_id.25b7=9bc50153-f819-4b18-8c34-8c84474dc2d5.1749314768.46.1751950590.1751905890.211afc14-634f-4c0e-97f0-6dd265b6cccb.e241178f-7bc9-4a0f-9506-9124ac1f2795.cd37744c-3b33-4db4-a1aa-4ae86776d5bd.1751950566782.17',
        'Origin': 'https://www.aviasales.kz',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Cookie': 'nuid=1a48fa2e-04b7-4192-a79e-8d4f5f26e513',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Priority': 'u=4',
        'TE': 'trailers',
    }

    payload = {
        "search_params": {
            "directions": [
                {"origin": "ALA", "destination": "DUB", "date": "2025-07-12", "is_origin_airport": False, "is_destination_airport": False},
                {"origin": "DUB", "destination": "ALA", "date": "2025-07-19", "is_origin_airport": False, "is_destination_airport": False}
            ],
            "passengers": {"adults": 1, "children": 0, "infants": 0},
            "trip_class": "Y"
        },
        "client_features": {"direct_flights": True, "brand_ticket": False, "top_filters": True, "badges": False, "tour_tickets": True, "assisted": True},
        "market_code": "kz",
        "marker": "direct",
        "citizenship": "KZ",
        "currency_code": "usd",
        "languages": {"ru": 1},
        "experiment_groups": {
            "usc-exp-showSupportLinkNavbar": "enabled", "usc-exp-priceAlertSubscriptionOnExplore": "treatment", 
            "serp-exp-uxFeedback": "on", "serp-exp-hotels": "on_prod", "guides-exp-feed": "on", 
            "usc-exp-marketChangeOfferWidget": "on", "usc-exp-emailSubscriptionForm": "footer_form", 
            "serp-exp-modalDirectFlights": "off", "serp-exp-serverFilters": "on", "ex-exp-mainCityVideo": "off", 
            "serp-exp-faresV2": "on", "serp-exp-disableSeatsAmenitiesFlightInfo": "on", "serp-exp-bletProposalsModal": "on", 
            "ex-exp-autocompleteRecommendations": "control", "usc-exp-marketChangeOfferForeigners": "treatment", 
            "serp-exp-nativeSharing": "on", "serp-exp-bletFlightInfo": "on", "serp-exp-hotelsMainAdPlacement": "on", 
            "serp-exp-bletInformers": "on", "serp-exp-faresFilters": "on", "asb-exp-additionalServicesOnContactForm": "control", 
            "asb-exp-migrateAssistedToSelene": "enabled", "serp-exp-bletItinerary": "on", "serp-exp-serverSecondaryBadges": "on", 
            "usc-exp-subscriptionLoginFlowWeb": "treatment", "serp-exp-sessionStartUxFeedback": "on_desktop", 
            "asb-exp-biletix-sbp": "on", "asb-exp-refund90Pricing": "off", "serp-exp-migrateRedirectPageToSelene": "on", 
            "serp-exp-migrateTicketModalToSelene": "on", "serp-exp-serverBannersOnTicket": "on", "asb-exp-servicesInFares": "off", 
            "serp-exp-filtersShortcuts": "on", "serp-exp-faqInTicket": "on", "ex-exp-cheapTicketsRTControl": "off", 
            "usc-exp-newForcedPopup": "control", "usc-exp-priceChartTooltipWeb": "control", "usc-exp-spaSupportHelp": "selene", 
            "ex-exp-spaMainPage": "selene", "ex-exp-hotTicketsBadges": "on", "tass-exp-airlineRulesAuth": "on", 
            "px-exp-welcomeOffer": "off", "ex-exp-noExactPricesScreen": "off", "asb-exp-offer-promo": "off", 
            "serp-exp-spaClickPage": "selene", "asb-exp-return90-onlineRegistration": "off", 
            "asb-exp-autofillDocsForOnePassenger": "off", "sce-exp-supportAssistant": "on", "tass-exp-airlineRules-v2": "on"
        },
        "debug": {"override_experiment_groups": {}},
        "brand": "AS"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        # Pretty-print the JSON response
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if e.response:
            print(f"Status Code: {e.response.status_code}")
            print("Response Content:")
            print(e.response.text)

if __name__ == "__main__":
    make_aviasales_request()