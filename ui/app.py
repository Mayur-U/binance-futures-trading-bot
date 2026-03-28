import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from bot.client import BinanceClient, BinanceAPIError, NetworkError
from bot.validators import validate_inputs
from bot.logging_config import setup_logging
import logging

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
setup_logging(log_dir=os.path.join(os.path.dirname(__file__), "../logs"))
logger = logging.getLogger(__name__)

app = Flask(__name__)

api_key    = os.getenv("BINANCE_API_KEY", "")
api_secret = os.getenv("BINANCE_API_SECRET", "")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/place_order", methods=["POST"])
def api_place_order():
    data = request.get_json()

    symbol     = data.get("symbol", "").strip().upper()
    side       = data.get("side", "").strip().upper()
    order_type = data.get("order_type", "").strip().upper()
    qty        = data.get("quantity")
    price      = data.get("price")
    stop_price = data.get("stop_price")

    # basic coercion
    try:
        qty = float(qty)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Quantity must be a number."}), 400

    price      = float(price)      if price      not in (None, "", 0) else None
    stop_price = float(stop_price) if stop_price not in (None, "", 0) else None

    # reuse the same validators from the CLI
    import io, contextlib
    validation_errors = []
    fake_out = io.StringIO()
    try:
        with contextlib.redirect_stdout(fake_out):
            validate_inputs(symbol, side, order_type, qty, price, stop_price)
    except SystemExit:
        validation_errors = [l.strip() for l in fake_out.getvalue().splitlines() if l.strip()]
        return jsonify({"success": False, "error": " | ".join(validation_errors)}), 400

    if not api_key or not api_secret:
        return jsonify({"success": False, "error": "API credentials not configured in .env"}), 500

    client = BinanceClient(api_key, api_secret)
    try:
        resp = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=price,
            stop_price=stop_price,
        )
        logger.info(f"UI order placed: {resp}")
        return jsonify({"success": True, "data": resp})
    except BinanceAPIError as e:
        logger.error(f"UI BinanceAPIError: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except NetworkError as e:
        logger.error(f"UI NetworkError: {e}")
        return jsonify({"success": False, "error": str(e)}), 503
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/logs")
def api_logs():
    log_dir = os.path.join(os.path.dirname(__file__), "../logs")
    lines = []
    try:
        files = sorted(os.listdir(log_dir), reverse=True)
        for fname in files[:3]:  # last 3 log files
            with open(os.path.join(log_dir, fname)) as f:
                lines += f.readlines()
    except Exception:
        pass
    # return last 60 lines, newest first
    return jsonify({"lines": list(reversed(lines[-60:]))})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
