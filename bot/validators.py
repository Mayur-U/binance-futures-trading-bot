import sys
import logging

logger = logging.getLogger(__name__)

VALID_SIDES       = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


def validate_inputs_dict(symbol: str, side: str, order_type: str,
                         quantity: float, price: float = None,
                         stop_price: float = None) -> list:
    errors = []

    if not symbol or not symbol.strip():
        errors.append("Symbol cannot be empty (e.g. BTCUSDT).")

    if side.upper() not in VALID_SIDES:
        errors.append(f"Invalid side '{side}'. Must be BUY or SELL.")

    if order_type.upper() not in VALID_ORDER_TYPES:
        errors.append(f"Invalid order type '{order_type}'. Choices: {', '.join(VALID_ORDER_TYPES)}.")

    if quantity <= 0:
        errors.append("Quantity must be greater than 0.")

    if order_type.upper() == "LIMIT":
        if price is None:
            errors.append("Price is required for LIMIT orders.")
        elif price <= 0:
            errors.append("Price must be greater than 0.")

    if order_type.upper() == "STOP_LIMIT":
        if price is None:
            errors.append("Price is required for STOP_LIMIT orders.")
        if stop_price is None:
            errors.append("Stop-price is required for STOP_LIMIT orders.")
        if price and stop_price and (price <= 0 or stop_price <= 0):
            errors.append("Price and stop-price must be greater than 0.")

    for e in errors:
        logger.error(f"Validation failed: {e}")

    return errors


def validate_inputs(symbol: str, side: str, order_type: str,
                    quantity: float, price: float = None, stop_price: float = None):
    errors = validate_inputs_dict(symbol, side, order_type, quantity, price, stop_price)
    if errors:
        for e in errors:
            print(f"  [!] {e}")
        sys.exit(1)
