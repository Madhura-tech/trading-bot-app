#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit SELL
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

# Stop-Market BUY (bonus order type)
python cli.py --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 95000

# Override API credentials inline (otherwise set env vars)
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET --symbol ETHUSDT --side BUY --type MARKET --quantity 0.01
"""

import argparse
import os
import sys

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger
from bot.orders import place_limit_order, place_market_order, place_stop_market_order
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Credentials — fall back to environment variables
    parser.add_argument(
        "--api-key",
        default=os.getenv("BINANCE_API_KEY", ""),
        help="Binance Testnet API key (or set BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_API_SECRET", ""),
        help="Binance Testnet API secret (or set BINANCE_API_SECRET env var)",
    )

    # Order parameters
    parser.add_argument("--symbol",   required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",     required=True, help="BUY or SELL")
    parser.add_argument("--type",     required=True, dest="order_type", help="MARKET | LIMIT | STOP_MARKET")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price",    default=None,  help="Limit price (required for LIMIT orders)")
    parser.add_argument("--stop-price", default=None, dest="stop_price",
                        help="Stop trigger price (required for STOP_MARKET orders)")
    parser.add_argument("--tif", default="GTC",
                        help="Time-in-force for LIMIT orders: GTC | IOC | FOK (default: GTC)")

    return parser


def run(args: argparse.Namespace) -> None:
    # ── Validate credentials ──────────────────────────────────────────
    if not args.api_key or not args.api_secret:
        print(
            "\n  [ERROR] API credentials missing.\n"
            "    Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
            "    or pass --api-key / --api-secret on the command line.\n"
        )
        sys.exit(1)

    # ── Validate inputs ───────────────────────────────────────────────
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.quantity)

        price      = validate_price(args.price)       if args.price      else None
        stop_price = validate_stop_price(args.stop_price) if args.stop_price else None

    except ValidationError as exc:
        logger.warning("Input validation failed: %s", exc)
        print(f"\n  [ERROR] Validation error: {exc}\n")
        sys.exit(1)

    # ── Cross-field validation ────────────────────────────────────────
    if order_type == "LIMIT" and price is None:
        print("\n  [ERROR] --price is required for LIMIT orders.\n")
        sys.exit(1)

    if order_type == "STOP_MARKET" and stop_price is None:
        print("\n  [ERROR] --stop-price is required for STOP_MARKET orders.\n")
        sys.exit(1)

    # ── Build client ──────────────────────────────────────────────────
    try:
        client = BinanceClient(api_key=args.api_key, api_secret=args.api_secret)
    except ValueError as exc:
        logger.error("Client init failed: %s", exc)
        print(f"\n  [ERROR] {exc}\n")
        sys.exit(1)

    # ── Dispatch to order function ────────────────────────────────────
    try:
        if order_type == "MARKET":
            place_market_order(client, symbol, side, quantity)

        elif order_type == "LIMIT":
            place_limit_order(client, symbol, side, quantity, price, time_in_force=args.tif)  # type: ignore[arg-type]

        elif order_type == "STOP_MARKET":
            place_stop_market_order(client, symbol, side, quantity, stop_price)  # type: ignore[arg-type]

    except BinanceAPIError:
        sys.exit(1)
    except (ConnectionError, TimeoutError) as exc:
        logger.error("Network failure: %s", exc)
        print(f"\n  [ERROR] Network error: {exc}\n")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Unexpected error: %s", exc)
        print(f"\n  [ERROR] Unexpected error: {exc}\n")
        sys.exit(1)


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
