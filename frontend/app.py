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
    html.Div([
        html.Label("Base:", style={"marginRight": "5px"}),
        dcc.Input(
            id="ticker-input-1",
            type="text",
            placeholder="Enter Primary Ticker (required)",
            debounce=True,
            value="IBIT",
            style={"marginRight": "10px"}
        ),
        html.Label("Top (optional):", style={"marginRight": "5px"}),
        dcc.Input(
            id="ticker-input-2",
            type="text",
            placeholder="Enter Second Ticker (optional)",
            debounce=True,
            value="",
            style={"marginRight": "10px"}
        ),
        html.Button("Submit", id="submit-button", n_clicks=0),
    ], style={"marginBottom": "10px"}),
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
        type="circle",
        children=html.Div(id="table-container"),
    ),
]))

@app.callback(
    Output("all-tables-data", "data"),
    Output("error-msg", "children"),
    Input("submit-button", "n_clicks"),
    State("ticker-input-1", "value"),
    State("ticker-input-2", "value"),
    prevent_initial_call=False,
)
def fetch_all_tables(n_clicks, ticker1, ticker2):
    if not ticker1:
        return dash.no_update, "Primary ticker is required."
    tickers = [ticker1.strip().upper()]
    if ticker2 and ticker2.strip() and ticker2.strip().upper() != ticker1.strip().upper():
        tickers.append(ticker2.strip().upper())
    try:
        endpoints = ["strikes", "forecast", "implied"]
        resp = requests.get(
            "http://localhost:8000/orats/multi",
            params={
                "ticker": ",".join(tickers),
                "endpoints": ",".join(endpoints)
            }
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

def make_vol_curve_chart(df_long):
    if df_long.empty:
        return html.Div("Missing required columns for chart.", style={"color": "red"})
    # Sort for consistent plotting
    expir_sorted = sorted(df_long["expirDate"].dropna().unique())
    df_long["expirDate"] = pd.Categorical(df_long["expirDate"], categories=expir_sorted, ordered=True)
    df_long = df_long.sort_values(["expirDate", "moneyness"], ascending=[True, False])
    fig = px.line(
        df_long,
        x="moneyness",
        y="value",
        color="expirDate",
        markers=True,
        title="Vol Curve by Expiry"
    )
    fig.update_layout(
        xaxis_title="Moneyness %",
        yaxis_title="Vol",
        xaxis_tickformat=".2%",
        yaxis_tickformat=".2%",
        xaxis_autorange='reversed'
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
    tickers = df["ticker"].unique() if "ticker" in df.columns else []

    # Filter by expiry if needed
    if expiry_filter and "expirDate" in df.columns:
        if isinstance(expiry_filter, list):
            df = df[df["expirDate"].isin(expiry_filter)]
        else:
            df = df[df["expirDate"] == expiry_filter]

    children = []

    if tab_value == "strikes":
        chart_divs = []
        table_divs = []
        for ticker in tickers:
            df_ticker = df[df["ticker"] == ticker]
            chart = make_strikes_chart(df_ticker)
            table = make_friendly_table(df_ticker)
            chart_divs.append(
                html.Div(
                    [
                        html.H4(f"{ticker}"),
                        chart,
                    ],
                    style={"margin": "10px"}
                )
            )
            table_divs.append(
                html.Div(
                    [
                        table
                    ],
                    style={"margin": "10px"}
                )
            )
        # Stack all charts, then all tables, in a single column
        return html.Div(chart_divs + table_divs)

    elif tab_value == "forecast":
        # One vol curve chart per ticker
        for ticker in tickers:
            df_ticker = df[df["ticker"] == ticker]
            df_long = melt_vol_curve(df_ticker)
            chart = make_vol_curve_chart(df_long)
            children.append(html.H4(f"{ticker}"))
            children.append(chart)

        # Spread chart (if two tickers)
        if len(tickers) == 2:
            t1, t2 = tickers[0], tickers[1]
            df1 = df[df["ticker"] == t1].copy()
            df2 = df[df["ticker"] == t2].copy()
            df1_long = melt_vol_curve(df1)
            df2_long = melt_vol_curve(df2)
            # Join on expirDate and moneyness
            join_cols = ["expirDate", "moneyness"]
            merged = pd.merge(
                df1_long, df2_long,
                on=join_cols,
                suffixes=(f"_{t1}", f"_{t2}")
            )
            
            # Calculate spread
            merged["value"] = merged[f"value_{t2}"].copy() - merged[f"value_{t1}"].copy()
            merged["ticker"] = f"{t2} - {t1} Spread"
            print(merged.head(20))
            spread_df = merged[["expirDate", "moneyness",f"value_{t1}", f"value_{t2}", "value", "ticker"]]
            
            # Chart the spread
            spread_chart = make_vol_curve_chart(spread_df)
            children.append(html.H4(f"{t2} - {t1} Spread"))
            children.append(spread_chart)
            spread_df["vol_spread"] = spread_df["value"].copy()
            spread_df.drop(columns=["value"], inplace=True)
            spread_df.rename(columns={"ticker": "spread_ticker"}, inplace=True)
            spread_table = make_friendly_table(spread_df)
            children.append(spread_table)

        # Table of all data
        table = make_friendly_table(df)
        children.append(table)
        return html.Div(children)

    elif tab_value == "implied":
        # One vol curve chart per ticker
        for ticker in tickers:
            df_ticker = df[df["ticker"] == ticker]
            df_long = melt_vol_curve(df_ticker)
            chart = make_vol_curve_chart(df_long)
            children.append(html.H4(f"{ticker}"))
            children.append(chart)
            # ATMIV chart for each ticker
            if "atmiv" in df_ticker.columns:
                atmiv_chart = make_atmiv_chart(df_ticker)
                children.append(html.H5(f"{ticker} ATMIV by Expiry"))
                children.append(atmiv_chart)

        # Spread charts (if two tickers)
        if len(tickers) == 2:
            t1, t2 = tickers[0], tickers[1]
            df1 = df[df["ticker"] == t1].copy()
            df2 = df[df["ticker"] == t2].copy()
            # Vol curve spread
            df1_long = melt_vol_curve(df1)
            df2_long = melt_vol_curve(df2)
            join_cols = ["expirDate", "moneyness"]
            merged = pd.merge(
                df1_long, df2_long,
                on=join_cols,
                suffixes=(f"_{t1}", f"_{t2}")
            )
            merged["value"] = merged[f"value_{t2}"] - merged[f"value_{t1}"]
            merged["ticker"] = f"{t2} - {t1} Spread"
            spread_df = merged[["expirDate", "moneyness", f"value_{t1}", f"value_{t2}", "value", "ticker"]]
            spread_chart = make_vol_curve_chart(spread_df)
            children.append(html.H4(f"{t2} - {t1} Vol Curve Spread"))
            children.append(spread_chart)

            # ATMIV spread chart
            if "atmiv" in df1.columns and "atmiv" in df2.columns:
                atmiv_merged = pd.merge(
                    df1[["expirDate", "atmiv"]], df2[["expirDate", "atmiv"]],
                    on="expirDate", suffixes=(f"_{t1}", f"_{t2}")
                )
                atmiv_merged["atmiv_spread"] = atmiv_merged[f"atmiv_{t2}"] - atmiv_merged[f"atmiv_{t1}"]
                atmiv_merged = atmiv_merged.sort_values("expirDate")
                # Plot the spread
                fig = px.line(
                    atmiv_merged,
                    x="expirDate",
                    y="atmiv_spread",
                    markers=True,
                    title=f"ATMIV Spread ({t2} - {t1}) by Expiry"
                )
                fig.update_layout(
                    xaxis_title="Expiry",
                    yaxis_title="ATMIV Spread",
                    yaxis_tickformat=".2%"
                )
                children.append(html.H5(f"{t2} - {t1} ATMIV Spread by Expiry"))
                children.append(dcc.Graph(figure=fig))

        # Table of all data
        table = make_friendly_table(df)
        children.append(table)
        return html.Div(children)

    # Default fallback
    table = make_friendly_table(df)
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

def melt_vol_curve(df):
    """Melt vol columns into long format with moneyness as a column."""
    vol_cols = [col for col in df.columns if col.startswith("vol")]
    if not vol_cols or "expirDate" not in df.columns:
        return pd.DataFrame()
    vol_cols_sorted = sorted(vol_cols, key=lambda x: int(x.replace("vol", "")))
    df_long = df.melt(
        id_vars=["expirDate", "ticker"] if "ticker" in df.columns else ["expirDate"],
        value_vars=vol_cols_sorted,
        var_name="vol",
        value_name="value"
    )
    df_long["moneyness"] = df_long["vol"].str.replace("vol", "").astype(float) / 100
    return df_long

if __name__ == "__main__":
    app.run(debug=True)