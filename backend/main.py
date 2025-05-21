import asyncio
import traceback
import pandas as pd

from starlite import Starlite, get, Response, Request
from typing import Any, Dict
from orats_api import (
    get_strikes, get_implied_monies, get_forecast_monies, get_summaries
)


ORATS_ENDPOINTS = {
    "strikes": get_strikes,
    "implied": get_implied_monies,
    "forecast": get_forecast_monies,
    # "summaries": get_summaries,
    # add more as needed
}

def df_to_response(df: pd.DataFrame) -> Response:
    return Response(content=df.to_json(orient="records"), media_type="application/json")

# orats api code 
@get("/orats/strikes")
def strikes_handler(ticker: str) -> Any:
    return get_strikes(ticker)

@get("/orats/implied")
def implied_handler(ticker: str) -> Any:
    return get_implied_monies(ticker)

@get("/orats/forecast")
def forecast_handler(ticker: str) -> Any:
    return get_forecast_monies(ticker)

@get("/orats/summaries")
def summaries_handler(ticker: str) -> Any:
    return get_summaries(ticker)

@get("/orats/multi")
async def orats_multi_handler(request: Request) -> Dict:
    ticker = request.query_params.get("ticker")
    endpoints = request.query_params.get("endpoints", "")
    endpoint_list = [e.strip() for e in endpoints.split(",") if e.strip()]
    results = {}

    async def call_func(ep):
        func = ORATS_ENDPOINTS.get(ep)
        if func:
            # If your functions are sync, run them in a thread pool using asyncio
            return ep, await asyncio.to_thread(func, ticker)
        return ep, {"error": "Unknown endpoint"}

    print("Query functions concurrently...")
    try:
        # Run all endpoint functions concurrently
        pairs = await asyncio.gather(*[call_func(ep) for ep in endpoint_list])
        # Unwrap if value is a dict with only a "data" key
        flat_results = {}
        for ep, value in pairs:
            if isinstance(value, dict) and set(value.keys()) == {"data"}:
                flat_results[ep] = value["data"]
            else:
                flat_results[ep] = value
        print("Done querying functions.")
        return flat_results
    except Exception as e:
        print(f"Error in orats_multi_handler: {e}")
        traceback.print_exc()
        return {"error": str(e)}
    
app = Starlite(route_handlers=[
     strikes_handler,
     implied_handler,
     forecast_handler,
     summaries_handler,
    orats_multi_handler
])