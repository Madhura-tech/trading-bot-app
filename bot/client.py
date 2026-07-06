import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logger

logger = setup_logger("client")

TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or an error payload."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures Testnet REST API.
    Handles request signing, sending, and basic error surfacing.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._session = requests.Session()
        self._session.headers.update({
            "X-MBX-APIKEY": self._api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append a HMAC-SHA256 signature to the parameter dict."""
        query = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _post(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["timestamp"] = self._timestamp()
        params = self._sign(params)
        url = f"{TESTNET_BASE_URL}{path}"

        logger.debug("POST %s | params: %s", url, {k: v for k, v in params.items() if k != "signature"})

        try:
            response = self._session.post(url, data=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error reaching Binance: %s", exc)
            raise ConnectionError(f"Cannot reach Binance testnet: {exc}") from exc
        except requests.exceptions.Timeout:
            logger.error("Request to %s timed out.", url)
            raise TimeoutError("Request to Binance timed out.")

        logger.debug("Response %s | body: %s", response.status_code, response.text)

        payload = response.json()

        if not response.ok or "code" in payload and payload["code"] != 200:
            code = payload.get("code", response.status_code)
            msg = payload.get("msg", response.text)
            logger.error("API error — code: %s, msg: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return payload

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        params = params or {}
        url = f"{TESTNET_BASE_URL}{path}"
        logger.debug("GET %s | params: %s", url, params)

        try:
            response = self._session.get(url, params=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error: %s", exc)
            raise ConnectionError(f"Cannot reach Binance testnet: {exc}") from exc

        logger.debug("Response %s | body: %s", response.status_code, response.text)

        if not response.ok:
            payload = response.json()
            raise BinanceAPIError(payload.get("code", response.status_code), payload.get("msg", ""))

        return response.json()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> Dict[str, Any]:
        """Fetch exchange info (symbol list, precision rules, etc.)."""
        return self._get("/fapi/v1/exchangeInfo")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Place a futures order.

        Parameters
        ----------
        symbol       : e.g. "BTCUSDT"
        side         : "BUY" or "SELL"
        order_type   : "MARKET", "LIMIT", or "STOP_MARKET"
        quantity     : order quantity
        price        : required for LIMIT orders
        stop_price   : required for STOP_MARKET orders
        time_in_force: "GTC" (default) | "IOC" | "FOK"
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("Stop price is required for STOP_MARKET orders.")
            params["stopPrice"] = str(stop_price)

        return self._post("/fapi/v1/order", params)
