# frontend/app.py
import dash
from dash import dcc, html, Input, Output, State, ctx, dash_table
import requests
import pandas as pd
import plotly.express as px
import io
import base64

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.H2("ORATS Dashboard via Starlite API"),
    dcc.Input(id="ticker-input", type="text", placeholder="Enter Ticker", debounce=True),
    html.Button("Submit", id="submit-button", n_clicks=0),
    html.Div(id="error-msg", style={"color": "red"}),
    dcc.Tabs(id="tabs", value="strikes", children=[
        dcc.Tab(label="Strikes", value="strikes"),
        dcc.Tab(label="Forecast", value="forecast"),
        dcc.Tab(label="Implied", value="implied")
    ]),
    html.Div(id="tab-content"),

    # HIDDEN dummy container to register all dynamic callback targets
    html.Div(style={"display": "none"}, children=[
        dash_table.DataTable(id="strike-table"),
        dash_table.DataTable(id="forecast-table"),
        dash_table.DataTable(id="implied-table"),
        dcc.Graph(id="strike-chart"),
        dcc.Graph(id="forecast-chart"),
        dcc.Graph(id="implied-chart")
    ])
])

# Layouts per tab
def render_table(tab_id):
    return html.Div([
        dcc.Loading(
            id=f"loading-{tab_id}",
            type="default",
            children=[
                dash_table.DataTable(
                    id=f"{tab_id}-table",
                    columns=[],
                    data=[],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "5px"},
                    export_format="csv"
                ),
                dcc.Graph(id=f"{tab_id}-chart")
            ]
        )
    ])

@app.callback(Output("tab-content", "children"), [Input("tabs", "value")])
def display_tab(tab):
    return render_table(tab)

@app.callback(
    [
        Output("strike-table", "data"),
        Output("strike-table", "columns"),
        Output("strike-chart", "figure"),
        Output("forecast-table", "data"),
        Output("forecast-table", "columns"),
        Output("forecast-chart", "figure"),
        Output("implied-table", "data"),
        Output("implied-table", "columns"),
        Output("implied-chart", "figure"),
        Output("error-msg", "children")
    ],
    [Input("submit-button", "n_clicks")],
    [State("ticker-input", "value")]
)
def update_all_tables(n_clicks, ticker):
    if not ticker:
        return [[], [], {}, [], [], {}, [], [], {}, ""]

    try:
        base_url = "http://localhost:8000/orats"
        endpoints = {
            "strike": f"{base_url}/strikes",
            "forecast": f"{base_url}/forecast",
            "implied": f"{base_url}/implied"
        }

        all_outputs = []

        for key in ["strike", "forecast", "implied"]:
            res = requests.get(endpoints[key], params={"ticker": ticker.upper()})
            res.raise_for_status()
            data = res.json().get("data", [])
            df = pd.DataFrame(data)
            if df.empty:
                all_outputs.extend([[], [], {}])
            else:
                columns = [{"name": col, "id": col} for col in df.columns]
                chart = px.line(df, x=df.columns[0], y=df.columns[-1], title=f"{key.capitalize()} Data Chart")
                all_outputs.extend([df.to_dict("records"), columns, chart])

        return all_outputs + [""]

    except Exception as e:
        return [[], [], {}, [], [], {}, [], [], {}, f"Error fetching data: {str(e)}"]

if __name__ == "__main__":
    app.run(debug=True)
