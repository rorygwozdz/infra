import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.dash_table.Format import Format, Scheme
import plotly.express as px
import requests
import pandas as pd
import dash_mantine_components as dmc

app = dash.Dash(__name__)
server = app.server

TABS = {
    "strikes": {"label": "Strikes", "endpoint": "strikes"},
    "forecast": {"label": "Forecast", "endpoint": "forecast"},
    "implied": {"label": "Implied", "endpoint": "implied"},
}

app.layout = dmc.MantineProvider(html.Div([
    html.H2("Vol Dashboard"),
    dcc.Input(
        id="ticker-input",
        type="text",
        placeholder="Enter Ticker",
        debounce=True,
        value="IBIT"  # <-- Set your default ticker here
    ),
    html.Button("Submit", id="submit-button", n_clicks=0),
    dmc.MultiSelect(
        id="expiry-filter",
        placeholder="Filter by Expiry Date(s)",
        data=[],  # Will be populated dynamically
        value=[],
        clearable=True,
        searchable=True,
        style={"width": 400, "marginBottom": 10},
    ),
    html.Div(id="error-msg", style={"color": "red"}),
    dcc.Tabs(
        id="tabs",
        value="strikes",
        children=[
            dcc.Tab(label=tab["label"], value=tab_id)
            for tab_id, tab in TABS.items()
        ]
    ),
    dcc.Store(id="all-tables-data"),
    dcc.Loading(
        id="loading-table",
        type="circle",  # or "default", "dot"
        children=html.Div(id="table-container"),
    ),
]))

@app.callback(
    Output("all-tables-data", "data"),
    Output("error-msg", "children"),
    Input("submit-button", "n_clicks"),
    Input("ticker-input", "value"),  
    prevent_initial_call=False,      # Allow callback to run on first load
)
def fetch_all_tables(n_clicks, ticker):
    if not ticker:
        return dash.no_update, ""
    try:
        # Pass a list of endpoints you want to fetch
        endpoints = ["strikes", "forecast", "implied"]
        resp = requests.get(
            "http://localhost:8000/orats/multi",
            params={"ticker": ticker.upper(), "endpoints": ",".join(endpoints)}
        )
        resp.raise_for_status()
        results = resp.json()
        return results, ""
    except Exception as e:
        return {}, f"Error fetching data: {str(e)}"

def make_strikes_chart(df):
    if all(x in df.columns for x in ["strike", "smvVol", "expirDate"]):
        # Sort expirDate and set as categorical for consistent ordering
        expir_sorted = sorted(df["expirDate"].dropna().unique())
        df["expirDate"] = pd.Categorical(df["expirDate"], categories=expir_sorted, ordered=True)
        if df[["strike", "smvVol", "expirDate"]].dropna().shape[0] == 0:
            return html.Div("No valid data for chart.", style={"color": "red"})
        fig = px.line(
            df,
            x="strike",
            y="smvVol",
            color="expirDate",
            markers=True,
            title="smvVol by Strike, grouped by Expiry"
        )
        return dcc.Graph(figure=fig)
    return html.Div("Missing required columns for chart.", style={"color": "red"})

def make_vol_curve_chart(df):
    vol_cols = [col for col in df.columns if col.startswith("vol")]
    vol_cols_sorted = sorted(vol_cols, key=lambda x: int(x.replace("vol", "")))
    if "expirDate" not in df.columns or not vol_cols_sorted:
        return html.Div("Missing required columns for chart.", style={"color": "red"})
    df_long = df.melt(id_vars=["expirDate"], value_vars=vol_cols_sorted,
                      var_name="vol", value_name="value")
    df_long["vol"] = df_long["vol"].str.replace("vol", "").astype(float) / 100
    df_long = df_long.sort_values(["expirDate", "vol"])
    # Use the same expirDate sorting as in make_strikes_chart
    expir_sorted = sorted(df_long["expirDate"].dropna().unique())
    df_long["expirDate"] = pd.Categorical(df_long["expirDate"], categories=expir_sorted, ordered=True)
    df_long = df_long.reset_index(drop=True)
    fig = px.line(
        df_long,
        x="vol",
        y="value",
        color="expirDate",
        markers=True,
        title="Vol Curve by Expiry"
    )
    fig.update_layout(
        xaxis_title="Moneyness %",
        yaxis_title="Vol",
        xaxis_tickformat=".2%",
        yaxis_tickformat=".2%"
    )
    return dcc.Graph(figure=fig)

def make_atmiv_chart(df):
    if "expirDate" not in df.columns or "atmiv" not in df.columns:
        return html.Div("Missing required columns for ATMIV chart.", style={"color": "red"})
    # Convert expirDate to datetime for correct x-axis ordering
    df = df.copy()
    df["expirDate"] = pd.to_datetime(df["expirDate"], errors="coerce")
    df = df.sort_values("expirDate")
    df["atmiv"] = pd.to_numeric(df["atmiv"], errors="coerce")
    fig = px.line(
        df,
        x="expirDate",
        y="atmiv",
        markers=True,
        title="ATMIV by Expiry"
    )
    fig.update_layout(
        xaxis_title="Expiry",
        yaxis_title="ATMIV",
        yaxis_tickformat=".2%"
    )
    return dcc.Graph(figure=fig)

def make_friendly_table(df):
    def is_percent_col(col):
        name = col.lower()
        # Must contain 'vol', 'iv', or 'rate', but NOT 'volume'
        return (
            (("vol" in name and "volume" not in name) or "iv" in name or "rate" in name)
        )

    columns = [
        {
            "name": col,
            "id": col,
            "type": "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "text",
            "format": (
                Format(precision=2, scheme=Scheme.percentage)
                if is_percent_col(col) and pd.api.types.is_numeric_dtype(df[col])
                else Format(precision=2, scheme=Scheme.fixed)
                if pd.api.types.is_float_dtype(df[col])
                else None
            ),
        }
        for col in df.columns
    ]

    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=columns,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "5px"},
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9"
            }
        ],
        export_format="csv"
    )

@app.callback(
    Output("table-container", "children"),
    Input("tabs", "value"),
    Input("all-tables-data", "data"),
    Input("expiry-filter", "value"),
)
def display_table(tab_value, all_tables_data, expiry_filter):
    if not all_tables_data or tab_value not in all_tables_data:
        return "No data found."
    data = all_tables_data[tab_value]
    df = pd.DataFrame(data)
    if expiry_filter and "expirDate" in df.columns:
        if isinstance(expiry_filter, list):
            df = df[df["expirDate"].isin(expiry_filter)]
        else:
            df = df[df["expirDate"] == expiry_filter]
    table = make_friendly_table(df)
    # Coerce strike and smvVol to numeric if present
    if "strike" in df.columns:
        df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
    if "smvVol" in df.columns:
        df["smvVol"] = pd.to_numeric(df["smvVol"], errors="coerce")
    table = make_friendly_table(df)
    if tab_value == "strikes":
        strikes_chart = make_strikes_chart(df)
        return html.Div([strikes_chart, table])
    elif tab_value == "forecast":
        vol_chart = make_vol_curve_chart(df)
        return html.Div([vol_chart, table])
    elif tab_value == "implied":
        vol_chart = make_vol_curve_chart(df)
        atmiv_chart = make_atmiv_chart(df)
        return html.Div([vol_chart, atmiv_chart, table])
    return table

@app.callback(
    Output("expiry-filter", "data"),
    Output("expiry-filter", "value"),
    Input("all-tables-data", "data"),
)
def update_expiry_options(all_tables_data):
    if not all_tables_data:
        return [], []
    expiries = set()
    for tab_data in all_tables_data.values():
        df = pd.DataFrame(tab_data)
        if "expirDate" in df.columns:
            expiries.update(df["expirDate"].dropna().unique())
    expiries = sorted(expiries)
    options = [{"label": e, "value": e} for e in expiries]
    return options, []

if __name__ == "__main__":
    app.run(debug=True)