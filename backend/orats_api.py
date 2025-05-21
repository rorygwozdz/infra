# backend/orats_api.py
import requests

BASE_URL = "https://api.orats.io/datav2"
API_TOKEN =  "df44ef7f-80ab-4508-924c-0e6d199723fc"

def _get(endpoint: str, params: dict = None):
    if params is None:
        params = {}
    params["token"] = API_TOKEN
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    return response.json()

def get_strikes(ticker: str):
    return _get("strikes", {"ticker": ticker})

def get_implied_monies(ticker: str):
    return _get("monies/implied", {"ticker": ticker})

def get_forecast_monies(ticker: str):
    return _get("monies/forecast", {"ticker": ticker})

def get_summaries(ticker: str):
    return _get("summaries", {"ticker": ticker})
