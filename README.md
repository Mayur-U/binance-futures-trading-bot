# Binance Testnet Trading Bot

Place BUY and SELL orders on Binance Testnet — USDT and USDC pairs only.
Supports both **Spot** testnet and **Futures** (USDT-M) testnet.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your API key and secret
```

**Spot testnet keys** → https://testnet.binance.vision  
**Futures testnet keys** → https://testnet.binancefuture.com

> Note: Spot and Futures testnet use **different** API keys.

---

## Web UI

```bash
python server.py
# open http://localhost:5000
```

- Toggle between **Spot** and **Futures** mode in the top bar
- Click USDT / USDC tab to switch quote asset
- Pick a coin chip (BTC, ETH, SOL…) or type a symbol manually
- Market, Limit, and Stop-Limit order types supported
- Live log viewer auto-refreshes every 5 seconds

---

## CLI

```bash
# Spot market buy BTCUSDT
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001

# Spot limit sell ETHUSDC
python cli.py --symbol ETHUSDC --side SELL --type LIMIT --qty 0.1 --price 2000

# Futures market buy (add --mode futures)
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.01 --mode futures
```

---

## Restrictions

- Only USDT and USDC quoted pairs are accepted (BTCUSDT, ETHUSDC, etc.)
- Any other quote asset is rejected at validation before hitting the API

---

## Structure

```
trading_bot/
├── bot/
│   ├── client.py          # REST client — supports spot + futures endpoints
│   ├── orders.py          # order placement + output
│   ├── validators.py      # USDT/USDC pair enforcement + input checks
│   └── logging_config.py
├── ui/index.html          # web dashboard
├── cli.py                 # CLI entry point
├── server.py              # Flask API server
├── requirements.txt
└── .env.example
```
