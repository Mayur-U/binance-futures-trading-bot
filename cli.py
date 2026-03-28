#!/usr/bin/env python3
import argparse
import os
import sys
from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient
from bot.validators import validate_inputs
from bot.orders import place_order


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.01
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --qty 0.1 --price 2000
  python cli.py --symbol BTCUSDT --side BUY  --type STOP_LIMIT --qty 0.01 --price 30500 --stop-price 30000
        """
    )
    parser.add_argument("--symbol",     required=True,  help="e.g. BTCUSDT")
    parser.add_argument("--side",       required=True,  help="BUY or SELL")
    parser.add_argument("--type",       required=True,  dest="order_type", help="MARKET / LIMIT / STOP_LIMIT")
    parser.add_argument("--qty",        required=True,  type=float)
    parser.add_argument("--price",      required=False, type=float, default=None)
    parser.add_argument("--stop-price", required=False, type=float, default=None, dest="stop_price")
    return parser


def main():
    load_dotenv()
    key    = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_API_SECRET")

    if not key or not secret:
        print("[!] BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env")
        sys.exit(1)

    log_path = setup_logging()
    print(f"Logging to: {log_path}\n")

    args = build_parser().parse_args()
    validate_inputs(args.symbol, args.side, args.order_type, args.qty, args.price, args.stop_price)

    client = BinanceClient(key, secret)
    place_order(client, args.symbol, args.side, args.order_type, args.qty, args.price, args.stop_price)


if __name__ == "__main__":
    main()
