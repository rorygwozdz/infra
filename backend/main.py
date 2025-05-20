from starlite import Starlite, get, Response
from backend.data import (
    get_vol_surface_df,
    get_vol_surface_percentiles_df,
    get_vol_spread_df,
    get_vol_spread_percentiles_df,
    get_top_down_vol_df,
    get_forward_vol_matrix_df,
)
import pandas as pd

def df_to_response(df: pd.DataFrame) -> Response:
    return Response(content=df.to_json(orient="records"), media_type="application/json")

@get("/vol-surface")
def vol_surface(stripped: bool = False) -> Response:
    df = get_vol_surface_df(stripped)
    return df_to_response(df)

@get("/vol-surface-percentiles")
def vol_surface_percentiles() -> Response:
    df = get_vol_surface_percentiles_df()
    return df_to_response(df)

@get("/vol-spread")
def vol_spread(stripped: bool = False) -> Response:
    df = get_vol_spread_df(stripped)
    return df_to_response(df)

@get("/vol-spread-percentiles")
def vol_spread_percentiles() -> Response:
    df = get_vol_spread_percentiles_df()
    return df_to_response(df)

@get("/top-down-vol")
def top_down_vol(stripped: bool = False) -> Response:
    df = get_top_down_vol_df(stripped)
    return df_to_response(df)

@get("/forward-vol-matrix")
def forward_vol_matrix(stripped: bool = False) -> Response:
    df = get_forward_vol_matrix_df(stripped)
    # for matrix, convert DataFrame to nested dict (row -> col -> value) for cleaner JSON
    matrix_dict = df.drop(columns=["Stripped"]).to_dict()
    return Response(content=pd.Series(matrix_dict).to_json(), media_type="application/json")

app = Starlite(route_handlers=[
    vol_surface,
    vol_surface_percentiles,
    vol_spread,
    vol_spread_percentiles,
    top_down_vol,
    forward_vol_matrix,
])
