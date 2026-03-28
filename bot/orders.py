import logging
from bot.client import BinanceClient, BinanceAPIError, NetworkError

logger = logging.getLogger(__name__)


def _needs_polling(resp: dict, order_type: str) -> bool:
    status   = resp.get("status", "")
    avg      = float(resp.get("avgPrice") or 0)
    executed = float(resp.get("executedQty") or 0)
    return order_type.upper() == "MARKET" and (status == "NEW" or avg == 0.0 or executed == 0.0)


def place_order(client: BinanceClient, symbol: str, side: str, order_type: str,
                quantity: float, price: float = None, stop_price: float = None) -> dict:

    print("\n---- Order Request ----")
    print(f"  Symbol    : {symbol.upper()}")
    print(f"  Side      : {side.upper()}")
    print(f"  Type      : {order_type.upper()}")
    print(f"  Quantity  : {quantity}")
    if price:      print(f"  Price     : {price}")
    if stop_price: print(f"  Stop Price: {stop_price}")
    print("-----------------------\n")

    logger.info(f"Placing {order_type.upper()} {side.upper()} {symbol} qty={quantity} price={price} stop={stop_price}")

    try:
        resp     = client.place_order(symbol=symbol, side=side, order_type=order_type,
                                      quantity=quantity, price=price, stop_price=stop_price)
        order_id = resp.get("orderId")

        if order_id and _needs_polling(resp, order_type):
            print("  [~] Order queued — polling for fill...")
            logger.info(f"Polling for fill: orderId={order_id}")
            resp = client.fetch_order_filled(symbol=symbol, order_id=order_id)

        _print_response(resp)
        logger.info(f"Final: orderId={resp.get('orderId')} status={resp.get('status')} avgPrice={resp.get('avgPrice')}")
        return resp

    except BinanceAPIError as e:
        print(f"\n[✗] API Error: {e}\n")
        logger.error(f"BinanceAPIError: {e}")
        return None
    except NetworkError as e:
        print(f"\n[✗] Network Error: {e}\n")
        logger.error(f"NetworkError: {e}")
        return None
    except ValueError as e:
        print(f"\n[✗] {e}\n")
        logger.error(f"ValueError: {e}")
        return None


def _print_response(resp: dict):
    avg = resp.get("avgPrice") or resp.get("price") or "0"
    print("---- Order Response ----")
    print(f"  Order ID    : {resp.get('orderId', 'N/A')}")
    print(f"  Status      : {resp.get('status', 'N/A')}")
    print(f"  Executed Qty: {resp.get('executedQty', '0')}")
    print(f"  Avg Price   : {avg}")
    print("------------------------")
    status = resp.get("status", "")
    if status == "FILLED":
        print("\n[✓] Order FILLED successfully!\n")
    elif status == "NEW":
        print("\n[✓] Order placed — sitting in order book\n")
    else:
        print(f"\n[✓] Order placed — status: {status}\n")
