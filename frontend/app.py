# frontend/app.py
import dash
from dash import dcc, html, Input, Output, State, ctx, dash_table
import requests
import pandas as pd

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H2("ORATS Strikes Viewer"),
    dcc.Input(id="ticker-input", type="text", placeholder="Enter Ticker", debounce=True),
    html.Button("Submit", id="submit-button", n_clicks=0),
    html.Div(id="error-msg", style={"color": "red"}),
    dcc.Loading(
        id="loading",
        type="default",
        children=dash_table.DataTable(
            id="strike-table",
            columns=[],
            data=[],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "5px"},
        )
    )
])

@app.callback(
    Output("strike-table", "data"),
    Output("strike-table", "columns"),
    Output("error-msg", "children"),
    Input("submit-button", "n_clicks"),
    State("ticker-input", "value"),
)

def update_table(n_clicks, ticker):
    if not ticker:
        return [], [], ""

    try:
        res = requests.get(f"http://localhost:8000/orats/strikes", params={"ticker": ticker.upper()})
        res.raise_for_status()
        data = res.json()["data"]
        df = pd.DataFrame(data)

        if df.empty:
            return [], [], f"No data found for {ticker.upper()}."

        columns = [{"name": col, "id": col} for col in df.columns]
        return df.to_dict("records"), columns, ""

    except Exception as e:
        return [], [], f"Error fetching data: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
