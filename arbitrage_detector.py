import websocket
import json
import itertools
import requests
from decimal import Decimal
from threading import Thread

class ArbitrageDetector:
    def __init__(self):
        """Initialize the ArbitrageDetector class."""
        self.book_ticker_data = {}  # Real-time bookTicker data of potential combinations
        self.result = {}  # Final result of assets with potential triangular arbitrage
        self.correct_triangles = []  # Triangles in correct form with only 3 assets and no circular pairs
        self.trading_pair_limit = 400  # Number of trading pairs to be fetched
        self.target_assets = ["BTC", "USDT", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "DOGE", "LTC", "LINK"]
        self.all_trading_pairs = self.fetch_trading_pairs(self.trading_pair_limit)
        self.correct_triangles = self.find_correct_triangles(self.all_trading_pairs)
        self.symbols = self.build_stream(self.correct_triangles)

    def fetch_trading_pairs(self, limit):
        """
        Fetch trading pairs from Binance API.

        Args:
            limit (int): Maximum number of trading pairs to fetch.

        Returns:
            list: List of trading pairs with their respective assets.
        """
        print("Fetching trading pairs...") # notify user via terminal
        initial_data = requests.get("https://api.binance.com/api/v3/exchangeInfo").json()
        capsules = []  # Capsules are in this format: {symbol: AB, left: A, right: B}
        for element in initial_data["symbols"]:
            if len(capsules) >= limit:
                break
            if element["baseAsset"] in self.target_assets or element["quoteAsset"] in self.target_assets:
                capsules.append({
                    "symbol": element["symbol"],
                    "left": element["baseAsset"],
                    "right": element["quoteAsset"]
                })
        return capsules

    def find_combinations_of_3(self, data):
        """
        Find all combinations of three items from the data.

        Args:
            data (list): List of trading pairs.

        Returns:
            list: List of combinations of three trading pairs.
        """
        return list(itertools.combinations(data, 3))

    def check_if_triangle(self, data):
        """
        Check if given combination of three forms a triangle: A->B->C->A.

        Args:
            data (list): List of trading pairs with their respective assets.

        Returns:
            int: Number of unique assets found in the initial data.
        """
        assets = {item["left"] for item in data}.union({item["right"] for item in data})
        return len(assets)

    def check_circular_pairs(self, data):
        """
        Check if there are circular pairs in the initial data: A->B, B->A

        Args:
            data (list): List of trading pairs with their respective assets.

        Returns:
            bool: True if no circular pairs are found, False otherwise.
        """
        for i in range(len(data)):
            for j in range(i + 1, len(data)):
                if (data[i]["left"] == data[j]["right"]) and (data[i]["right"] == data[j]["left"]):
                    return False
        return True

    def find_correct_triangles(self, all_trading_pairs):
        """
        Fetch trading pairs that have potential triangular arbitrage opportunities.

        Args:
            all_trading_pairs (list): List of trading pairs.

        Returns:
            list: List of valid potential triangular arbitrage opportunities.
        """
        print("Finding valid triangles...") # notify user via terminal
        combinations = self.find_combinations_of_3(all_trading_pairs)
        correct_triangles = []
        for combination in combinations:
            if self.check_if_triangle(combination) == 3 and self.check_circular_pairs(combination):
                correct_triangles.append(combination)
        return correct_triangles

    def build_stream(self, correct_triangles):
        """
        Build the WebSocket stream string from combinations to fetch book tickers.

        Args:
            correct_triangles (list): List of valid triangular arbitrage trading pairs.

        Returns:
            str: WebSocket stream string.
        """
        print("Building the book ticker stream...") # notify user via terminal
        trading_pairs = {item["symbol"].lower() for triangle in correct_triangles for item in triangle}
        return "/".join([f"{pair}@bookTicker" for pair in trading_pairs])

    def fetch_book_ticker_data(self, symbols):
        """
        Fetch real-time book ticker data from Binance using WebSocket.

        Args:
            symbols (str): A string of trading pair symbols for the WebSocket stream.
        """
        print("Gathering book ticker data...") # notify user via terminal
        socket = f"wss://stream.binance.com:9443/stream?streams={symbols}"
        ws = websocket.WebSocketApp(socket, on_message=self.on_message, on_close=self.on_close, on_error=self.on_error)
        ws.run_forever()

    def on_message(self, ws, message):
        """
        Handle incoming WebSocket messages.

        Args:
            ws (WebSocketApp): WebSocket application instance.
            message (str): Message received from the WebSocket.
        """
        message_json = json.loads(message)
        data = message_json["data"]
        self.book_ticker_data[data["s"]] = data  # Get latest book ticker data

        for target in self.correct_triangles:
            count = sum(1 for trading_pair in target if trading_pair["symbol"] in self.book_ticker_data)
            if count == 3:
                self.calculate_triangular_arbitrage(target)

    def on_close(self, ws):
        """Handle WebSocket close event."""
        print("Connection Terminated")

    def on_error(self, ws, error):
        """
        Handle WebSocket error event.

        Args:
            ws (WebSocketApp): WebSocket application instance.
            error (str): Error message received from the WebSocket.
        """
        print(error)

    def calculate_triangular_arbitrage(self, trading_pairs):
        """
        Calculate triangular arbitrage based on the trading pairs.

        Args:
            trading_pairs (list): List of trading pairs involved in a potential triangular arbitrage.
        """
        AB, BC, AC = None, None, None
        for count1, element1 in enumerate(trading_pairs):
            for count2, element2 in enumerate(trading_pairs):
                if element1["right"] == element2["left"]:
                    AB = element1
                    BC = element2
                    AC = trading_pairs[len(trading_pairs) - count1 - count2]
                    break
            if AC is not None:
                break

        ask_AB = Decimal(self.book_ticker_data[AB["symbol"]]["a"])  # Ask and bid values of AB
        bid_AB = Decimal(self.book_ticker_data[AB["symbol"]]["b"])

        ask_BC = Decimal(self.book_ticker_data[BC["symbol"]]["a"])  # Ask and bid values of BC
        bid_BC = Decimal(self.book_ticker_data[BC["symbol"]]["b"])

        ask_AC = Decimal(self.book_ticker_data[AC["symbol"]]["a"])  # Ask and bid values of AC
        bid_AC = Decimal(self.book_ticker_data[AC["symbol"]]["b"])

        condition1 = (ask_AB * ask_BC) * (1 / bid_AC)
        condition2 = (bid_AB * bid_BC) * (1 / ask_AC)

        arbitrage_code = f"{AB['left']}-{AB['right']}-{BC['right']}"  # Triangle code, A-B-C

        if condition1 < 1 or condition2 > 1:  # If arbitrage exists
            self.result[arbitrage_code] = [f"{AB['symbol']}: {ask_AB}\n{BC['symbol']}: {ask_BC}\n{AC['symbol']}: {ask_AC}\n",
                                           f"{AB['symbol']}: {bid_AB}\n{BC['symbol']}: {bid_BC}\n{AC['symbol']}: {bid_AC}\n",
                                           "YES"]
        else:  # If arbitrage doesn't exist
            self.result[arbitrage_code] = [f"{AB['symbol']}: {ask_AB}\n{BC['symbol']}: {ask_BC}\n{AC['symbol']}: {ask_AC}\n",
                                           f"{AB['symbol']}: {bid_AB}\n{BC['symbol']}: {bid_BC}\n{AC['symbol']}: {bid_AC}\n",
                                           "NO"]

    def start(self):
        """Start the WebSocket connection to fetch real-time book ticker data."""
        real_time_data_thread = Thread(target=self.fetch_book_ticker_data, args=(self.symbols,))
        real_time_data_thread.start()