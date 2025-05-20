import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

expiries = pd.date_range(datetime.today(), periods=6, freq='ME')
deltas = ["10", "25", "50", "75", "90"]
lookbacks = ["1m", "3m", "6m", "1y", "3y", "5y"]
instruments = ["AAPL", "MSFT", "SPY", "QQQ", "TopDown"]

def get_vol_surface_df(stripped: bool = False) -> pd.DataFrame:
    data = []
    for expiry in expiries:
        for delta in deltas:
            base_vol = np.random.uniform(0.2, 0.6)
            vol = base_vol * (0.95 if stripped else 1.0)
            data.append({
                "Expiry": expiry.strftime("%Y-%m-%d"),
                "Delta": delta,
                "Current Vol": round(vol, 4),
                "N-day Vol Change": round(np.random.uniform(-0.05, 0.05), 4),
                "Stripped": stripped,
            })
    return pd.DataFrame(data)

def get_vol_surface_percentiles_df() -> pd.DataFrame:
    data = []
    for expiry in expiries:
        for delta in deltas:
            for lb in lookbacks:
                data.append({
                    "Expiry": expiry.strftime("%Y-%m-%d"),
                    "Delta": delta,
                    "Lookback": lb,
                    "Percentile": round(np.random.uniform(0, 100), 2)
                })
    return pd.DataFrame(data)

def get_vol_spread_df(stripped: bool = False) -> pd.DataFrame:
    data = []
    for expiry in expiries:
        for delta in deltas:
            base_spread = np.random.uniform(-0.05, 0.05)
            spread = base_spread * (0.9 if stripped else 1.0)
            data.append({
                "Expiry": expiry.strftime("%Y-%m-%d"),
                "Delta": delta,
                "Current Vol Spread": round(spread, 4),
                "N-day Vol Spread Change": round(np.random.uniform(-0.03, 0.03), 4),
                "Stripped": stripped,
            })
    return pd.DataFrame(data)

def get_vol_spread_percentiles_df() -> pd.DataFrame:
    data = []
    for expiry in expiries:
        for delta in deltas:
            for lb in lookbacks:
                data.append({
                    "Expiry": expiry.strftime("%Y-%m-%d"),
                    "Delta": delta,
                    "Lookback": lb,
                    "Percentile": round(np.random.uniform(0, 100), 2)
                })
    return pd.DataFrame(data)

def get_top_down_vol_df(stripped: bool = False) -> pd.DataFrame:
    metrics = ["Current", "N-day Vol Change", "Dirty Correlation", "N-day Dirty Correlation Change"]
    data = []
    for expiry in expiries:
        for metric in metrics:
            val = np.random.uniform(0, 0.6)
            if stripped:
                val *= 0.9
            for lb in lookbacks:
                data.append({
                    "Expiry": expiry.strftime("%Y-%m-%d"),
                    "Metric": metric,
                    "Value": round(val, 4),
                    "Lookback": lb,
                    "Stripped": stripped,
                })
    return pd.DataFrame(data)

def get_forward_vol_matrix_df(stripped: bool = False) -> pd.DataFrame:
    size = len(instruments)
    base_matrix = np.random.uniform(0.2, 0.6, size=(size, size))
    if stripped:
        base_matrix *= 0.9
    df = pd.DataFrame(base_matrix, index=instruments, columns=instruments)
    df["Stripped"] = stripped
    return df

