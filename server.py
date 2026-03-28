#!/usr/bin/env python3
import os
import glob
import logging
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError, NetworkError
from bot.validators import validate_inputs_dict
from bot.orders import _needs_polling

load_dotenv()
setup_logging()

logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("bot.server")
app    = Flask(__name__, static_folder="ui", static_url_path="")


def get_client():
    key    = os.getenv("BINANCE_API_KEY")
    secret = os.getenv("BINANCE_API_SECRET")
    if not key or not secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET are not set in .env")
    return BinanceClient(key, secret)


def _normalize_avg(resp: dict) -> str:
    avg = float(resp.get("avgPrice") or 0)
    if avg > 0:
        return f"{avg:.4f}"
    return "0"


@app.route("/")
def index():
    return send_from_directory("ui", "index.html")


@app.route("/api/order", methods=["POST"])
def place_order():
    body = request.get_json(force=True)

    symbol     = (body.get("symbol")     or "").strip().upper()
    side       = (body.get("side")       or "").strip().upper()
    order_type = (body.get("order_type") or "").strip().upper()
    qty_raw    = body.get("quantity")
    price_raw  = body.get("price")
    stop_raw   = body.get("stop_price")

    try:
        quantity = float(qty_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Quantity must be a number."}), 400

    price      = float(price_raw) if price_raw not in (None, "", "0") else None
    stop_price = float(stop_raw)  if stop_raw  not in (None, "", "0") else None

    errors = validate_inputs_dict(symbol, side, order_type, quantity, price, stop_price)
    if errors:
        return jsonify({"ok": False, "error": " | ".join(errors)}), 400

    try:
        client = get_client()
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    try:
        logger.info(f"Placing {order_type} {side} {symbol} qty={quantity}")
        resp     = client.place_order(symbol=symbol, side=side, order_type=order_type,
                                      quantity=quantity, price=price, stop_price=stop_price)
        order_id = resp.get("orderId")

        if order_id and _needs_polling(resp, order_type):
            logger.info(f"Order {order_id} is NEW — polling for fill...")
            resp = client.fetch_order_filled(symbol=symbol, order_id=order_id)
            logger.info(f"After poll: status={resp.get('status')} avgPrice={resp.get('avgPrice')}")

        return jsonify({
            "ok":           True,
            "order_id":     resp.get("orderId"),
            "status":       resp.get("status"),
            "executed_qty": resp.get("executedQty", "0"),
            "avg_price":    _normalize_avg(resp),
            "symbol":       resp.get("symbol"),
            "side":         resp.get("side"),
            "type":         resp.get("type"),
            "raw":          resp,
        })

    except BinanceAPIError as e:
        logger.error(f"BinanceAPIError: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400
    except NetworkError as e:
        logger.error(f"NetworkError: {e}")
        return jsonify({"ok": False, "error": str(e)}), 503
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/logs")
def get_logs():
    n     = int(request.args.get("lines", 80))
    files = sorted(glob.glob("logs/trading_bot_*.log"))
    if not files:
        return jsonify({"lines": []})
    with open(files[-1]) as f:
        lines = f.readlines()
    return jsonify({"lines": [l.rstrip() for l in lines[-n:]], "file": files[-1]})


if __name__ == "__main__":
    print("\n  Trading Bot UI → http://localhost:5000\n")
    app.run(debug=False, port=5000)
