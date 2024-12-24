
# Crypto Trading Bot
# This script is designed to automate crypto trading on Binance Futures.
# It dynamically calculates position sizes, sets leverage, and executes trades based on account balance and risk management principles.

import time
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Binance API Keys
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

# Initialize Binance Client
client = Client(API_KEY, API_SECRET)

# Trading Symbols
SYMBOLS = ["DOGEUSDT", "BNBUSDT"]

# Trading Parameters
DEFAULT_LEVERAGE = 10  # Default leverage for all symbols
RISK_PER_TRADE = 0.01  # 1% of account balance
RETRY_LIMIT = 5  # Retry limit for API errors
RETRY_DELAY = 5  # Delay between retries in seconds

# Fetch Account Balance
def get_balance():
    try:
        balance = client.futures_account_balance()
        usdt_balance = next(item for item in balance if item["asset"] == "USDT")
        return float(usdt_balance["balance"])
    except BinanceAPIException as e:
        print(f"Error fetching balance: {e}")
        return 0.0

# Fetch Symbol Precision
def get_symbol_info(symbol):
    try:
        info = client.futures_exchange_info()
        symbol_info = next(item for item in info["symbols"] if item["symbol"] == symbol)
        step_size = float(next(filter(lambda x: x["filterType"] == "LOT_SIZE", symbol_info["filters"]))["stepSize"])
        return step_size
    except Exception as e:
        print(f"Error fetching symbol info for {symbol}: {e}")
        return None

# Set Leverage
def set_leverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        print(f"Leverage set to {leverage}x for {symbol}")
    except BinanceAPIException as e:
        print(f"Error setting leverage for {symbol}: {e}")

# Calculate Position Size
def calculate_position_size(balance, price, step_size):
    risk_amount = balance * RISK_PER_TRADE
    position_size = risk_amount / price
    # Round position size to the nearest valid step size
    position_size = round(position_size / step_size) * step_size
    return position_size

# Place Market Order
def place_order(symbol, side, quantity):
    retries = 0
    while retries < RETRY_LIMIT:
        try:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
            print(f"Order placed: {symbol} - {side} {quantity}")
            return order
        except BinanceAPIException as e:
            print(f"API error: {e}. Retrying in {RETRY_DELAY} seconds...")
            retries += 1
            time.sleep(RETRY_DELAY)
    print(f"Max retries reached. Exiting for {symbol}.")
    return None

# Main Trading Logic
def trade():
    balance = get_balance()
    if balance <= 0:
        print("Insufficient balance to trade.")
        return

    for symbol in SYMBOLS:
        try:
            ticker = client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            step_size = get_symbol_info(symbol)

            if not step_size:
                print(f"Skipping {symbol} due to missing symbol info.")
                continue

            position_size = calculate_position_size(balance, price, step_size)

            if position_size <= 0:
                print(f"Position size for {symbol} is too small. Skipping.")
                continue

            set_leverage(symbol, DEFAULT_LEVERAGE)

            # Place Buy and Sell Orders
            place_order(symbol, "BUY", position_size)
            place_order(symbol, "SELL", position_size)

        except BinanceAPIException as e:
            print(f"Error fetching price for {symbol}: {e}")
        except Exception as e:
            print(f"Unexpected error for {symbol}: {e}")

# Run the Bot
if __name__ == "__main__":
    print("Starting Binance Futures Trading Bot...")
    while True:
        trade()
        print("Sleeping for 5 minutes...")
        time.sleep(300)
