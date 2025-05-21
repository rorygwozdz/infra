import dash
from dash import dcc, html, Input, Output, State, dash_table
import requests
import pandas as pd

app = dash.Dash(__name__)
server = app.server

TABS = {
    "strikes": {"label": "Strikes", "endpoint": "strikes"},
    "forecast": {"label": "Forecast", "endpoint": "forecast"},
    "implied": {"label": "Implied", "endpoint": "implied"},
}

app.layout = html.Div([
    html.H2("Vol Dashboard"),
    dcc.Input(id="ticker-input", type="text", placeholder="Enter Ticker", debounce=True),
    html.Button("Submit", id="submit-button", n_clicks=0),
    html.Div(id="error-msg", style={"color": "red"}),
    dcc.Tabs(
        id="tabs",
        value="strikes",
        children=[
            dcc.Tab(label=tab["label"], value=tab_id)
            for tab_id, tab in TABS.items()
        ]
    ),
    dcc.Store(id="all-tables-data"),  # Hidden store for all tables' data
    html.Div(id="table-container"),
])

@app.callback(
    Output("all-tables-data", "data"),
    Output("error-msg", "children"),
    Input("submit-button", "n_clicks"),
    State("ticker-input", "value"),
)
def fetch_all_tables(n_clicks, ticker):
    if not ticker:
        return dash.no_update, ""
    results = {}
    try:
        for tab_id, tab in TABS.items():
            url = f"http://localhost:8000/orats/{tab['endpoint']}"
            resp = requests.get(url, params={"ticker": ticker.upper()})
            resp.raise_for_status()
            data_json = resp.json()
            data = data_json.get("data", data_json)
            results[tab_id] = data
        return results, ""
    except Exception as e:
        return {}, f"Error fetching data: {str(e)}"

@app.callback(
    Output("table-container", "children"),
    Input("tabs", "value"),
    Input("all-tables-data", "data"),
)
def display_table(tab_value, all_tables_data):
    if not all_tables_data or tab_value not in all_tables_data:
        return "No data found."
    data = all_tables_data[tab_value]
    df = pd.DataFrame(data)
    if df.empty:
        return "No data found."
    columns = [{"name": col, "id": col} for col in df.columns]
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=columns,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "5px"},
        export_format="csv"
    )

if __name__ == "__main__":
    app.run(debug=True)