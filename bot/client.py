import hashlib
import hmac
import time
import logging
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

FUTURES_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.base_url   = FUTURES_URL

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        sig = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        params["signature"] = sig
        return params

    def _post(self, endpoint: str, params: dict) -> dict:
        signed = self._sign(params)
        url    = self.base_url + endpoint
        safe   = {k: v for k, v in params.items() if k != "signature"}
        logger.info(f"POST {endpoint} | {safe}")
        try:
            resp = self.session.post(url, data=signed, timeout=10)
            data = resp.json()
            logger.info(f"Response [{resp.status_code}]: {data}")
            resp.raise_for_status()
            return data
        except requests.exceptions.HTTPError:
            raise BinanceAPIError(data.get("msg", "Unknown API error"), data.get("code", -1))
        except requests.exceptions.ConnectionError:
            raise NetworkError("Could not reach Binance Futures testnet. Check your internet.")
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out.")

    def _get(self, endpoint: str, params: dict) -> dict:
        signed = self._sign(params)
        url    = self.base_url + endpoint
        logger.info(f"GET {endpoint} | orderId={params.get('orderId')}")
        try:
            resp = self.session.get(url, params=signed, timeout=10)
            data = resp.json()
            logger.info(f"Response [{resp.status_code}]: {data}")
            resp.raise_for_status()
            return data
        except requests.exceptions.HTTPError:
            raise BinanceAPIError(data.get("msg", "Unknown API error"), data.get("code", -1))
        except requests.exceptions.ConnectionError:
            raise NetworkError("Could not reach Binance Futures testnet.")
        except requests.exceptions.Timeout:
            raise NetworkError("Request timed out.")

    def place_order(self, symbol: str, side: str, order_type: str,
                    quantity: float, price: float = None, stop_price: float = None) -> dict:
        params = {
            "symbol":   symbol.upper(),
            "side":     side.upper(),
            "type":     order_type.upper(),
            "quantity": quantity,
        }

        if order_type.upper() == "LIMIT":
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"]       = price
            params["timeInForce"] = "GTC"

        elif order_type.upper() == "STOP_LIMIT":
            if price is None or stop_price is None:
                raise ValueError("Both --price and --stop-price are required for STOP_LIMIT.")
            params["price"]       = price
            params["stopPrice"]   = stop_price
            params["timeInForce"] = "GTC"
            params["type"]        = "STOP"

        return self._post("/fapi/v1/order", params)

    def fetch_order(self, symbol: str, order_id: int) -> dict:
        return self._get("/fapi/v1/order", {"symbol": symbol.upper(), "orderId": order_id})

    def fetch_order_filled(self, symbol: str, order_id: int,
                           max_attempts: int = 6, delay: float = 0.8) -> dict:
        for attempt in range(max_attempts):
            order  = self.fetch_order(symbol, order_id)
            status = order.get("status", "")
            logger.info(f"Poll #{attempt+1} orderId={order_id} status={status} avgPrice={order.get('avgPrice')}")
            if status in ("FILLED", "CANCELED", "EXPIRED", "REJECTED"):
                return order
            if attempt < max_attempts - 1:
                time.sleep(delay)
        return order


class BinanceAPIError(Exception):
    def __init__(self, message: str, code: int = -1):
        self.code = code
        super().__init__(f"Binance API error {code}: {message}")


class NetworkError(Exception):
    pass
