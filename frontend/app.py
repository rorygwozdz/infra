import dash
from dash import html, dcc, Input, Output
import requests
import pandas as pd
import plotly.express as px

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Vol Surface Dashboard"),
    dcc.Interval(id="interval", interval=10*1000, n_intervals=0),  # refresh every 10 seconds
    dcc.Graph(id="vol-surface-graph"),
])

@app.callback(
    Output("vol-surface-graph", "figure"),
    Input("interval", "n_intervals"),
)
def update_vol_surface(_):
    url = "http://localhost:8000/vol-surface"
    res = requests.get(url)
    data = res.json()
    df = pd.DataFrame(data)
    fig = px.line(df, x="Expiry", y="Volatility", color="Delta", title="Single Name Vol Surface")
    return fig

if __name__ == "__main__":
    app.run(debug=True)
