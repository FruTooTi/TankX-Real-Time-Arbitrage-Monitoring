import threading
from dash import dcc, html, dash_table, Input, Output, Dash
import pandas as pd
import webbrowser
import requests
import time
from arbitrage_detector import ArbitrageDetector

def open_browser():
    """Open the default web browser to the Dash app when the application runs."""
    while True:
        try:
            response = requests.get("http://127.0.0.1:8050")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
    webbrowser.open("http://127.0.0.1:8050/")

def initialize_dash_app(result):
    """Initialize the Dash application for displaying real-time arbitrage opportunities."""
    app = Dash(__name__)
    app.layout = html.Div(children=[
        html.H1(children='Real-Time Binance Book Ticker Data'),
        dash_table.DataTable(
            id='live-update-table',
            columns=[
                {'name': 'Assets', 'id': 'assets'},
                {'name': 'Ask Price', 'id': 'ask_price'},
                {'name': 'Bid Price', 'id': 'bid_price'},
                {'name': 'Triangular Arbitrage', 'id': 'triangular_arbitrage'}
            ],
            data=[]
        ),
        dcc.Interval(
            id='interval-component',
            interval=1*100,  # Update every 0.1 seconds, minimizing the delay for real-time data
            n_intervals=0
        )
    ])

    @app.callback(Output('live-update-table', 'data'),
                  [Input('interval-component', 'n_intervals')])
    def update_table(n):
        """Update the table with the latest arbitrage data."""
        display_data = [
            {
                "assets": element,
                "ask_price": result[element][0],
                "bid_price": result[element][1],
                "triangular_arbitrage": result[element][2]
            }
            for element in result.keys()
        ]
        return pd.DataFrame(display_data).to_dict('records')

    return app

if __name__ == '__main__':
    detector = ArbitrageDetector()
    detector.start()

    app = initialize_dash_app(detector.result)
    threading.Thread(target=open_browser).start()
    app.run_server(debug=True)