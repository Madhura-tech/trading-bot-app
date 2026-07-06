from decimal import Decimal
from typing import Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logger

logger = setup_logger("orders")


def _print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal],
    stop_price: Optional[Decimal],
) -> None:
    """Print a human-readable summary of what is about to be sent."""
    print("\n" + "=" * 50)
    print("  ORDER REQUEST SUMMARY")
    print("=" * 50)
    print(f"  Symbol     : {symbol}")
    print(f"  Side       : {side}")
    print(f"  Type       : {order_type}")
    print(f"  Quantity   : {quantity}")
    if price is not None:
        print(f"  Price      : {price}")
    if stop_price is not None:
        print(f"  Stop Price : {stop_price}")
    print("=" * 50 + "\n")


def _print_order_response(response: dict) -> None:
    """Print the key fields from the Binance order response."""
    print("\n" + "=" * 50)
    print("  ORDER RESPONSE")
    print("=" * 50)
    print(f"  Order ID     : {response.get('orderId', 'N/A')}")
    print(f"  Client OID   : {response.get('clientOrderId', 'N/A')}")
    print(f"  Symbol       : {response.get('symbol', 'N/A')}")
    print(f"  Status       : {response.get('status', 'N/A')}")
    print(f"  Side         : {response.get('side', 'N/A')}")
    print(f"  Type         : {response.get('type', 'N/A')}")
    print(f"  Orig Qty     : {response.get('origQty', 'N/A')}")
    print(f"  Executed Qty : {response.get('executedQty', 'N/A')}")
    avg_price = response.get("avgPrice") or response.get("price", "N/A")
    print(f"  Avg Price    : {avg_price}")
    print(f"  Time         : {response.get('updateTime', 'N/A')}")
    print("=" * 50 + "\n")


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
) -> dict:
    """Place a MARKET order and return the response dict."""
    _print_order_summary(symbol, side, "MARKET", quantity, None, None)
    logger.info("Placing MARKET %s order | symbol=%s qty=%s", side, symbol, quantity)

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
        )
    except BinanceAPIError as exc:
        logger.error("MARKET order failed | %s", exc)
        print(f"\n  [FAILED] {exc.message}\n")
        raise

    _print_order_response(response)
    logger.info(
        "MARKET order placed | orderId=%s status=%s executedQty=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
    )
    print("  [OK] Order placed successfully!\n")
    return response


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> dict:
    """Place a LIMIT order and return the response dict."""
    _print_order_summary(symbol, side, "LIMIT", quantity, price, None)
    logger.info(
        "Placing LIMIT %s order | symbol=%s qty=%s price=%s tif=%s",
        side, symbol, quantity, price, time_in_force,
    )

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
        )
    except BinanceAPIError as exc:
        logger.error("LIMIT order failed | %s", exc)
        print(f"\n  [FAILED] {exc.message}\n")
        raise

    _print_order_response(response)
    logger.info(
        "LIMIT order placed | orderId=%s status=%s",
        response.get("orderId"),
        response.get("status"),
    )
    print("  [OK] Order placed successfully!\n")
    return response


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> dict:
    """Place a STOP_MARKET order (bonus order type) and return the response dict."""
    _print_order_summary(symbol, side, "STOP_MARKET", quantity, None, stop_price)
    logger.info(
        "Placing STOP_MARKET %s order | symbol=%s qty=%s stopPrice=%s",
        side, symbol, quantity, stop_price,
    )

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type="STOP_MARKET",
            quantity=quantity,
            stop_price=stop_price,
        )
    except BinanceAPIError as exc:
        logger.error("STOP_MARKET order failed | %s", exc)
        print(f"\n  [FAILED] {exc.message}\n")
        raise

    _print_order_response(response)
    logger.info(
        "STOP_MARKET order placed | orderId=%s status=%s",
        response.get("orderId"),
        response.get("status"),
    )
    print("  [OK] Order placed successfully!\n")
    return response
