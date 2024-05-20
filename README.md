# TankX Triangular Arbitrage CStudy
This Python project regarding Real-Time Arbitrage Monitoring is designed as a solution for TankX's "Real-Time Arbitrage Monitoring" case study. The project has been optimized for highest efficiency possible using several optimization methods by utilizing several python libraries and integrated methods. For a better analysis, a subset of trading pairs with the highest arbitrage potential has been selected. For such filtering of trading pairs, special attention was paid to select assets with higher volatility and higher volume in the trade market.

The visualization of triangular arbitrages has been established using dash and basic html. For real-time data, websockets was effectively utilized.

In order to run the application, you are required to have the following python libraries are required:

- websocket
- json
- itertools
- requests
- pandas
- dash
- webbrowser
- time
- threading

Make sure to have the libraries installed using "pip install"
