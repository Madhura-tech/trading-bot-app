# Binance Futures Testnet Trading Bot

A minimal, well-structured Python CLI application that places orders on the
Binance Futures Testnet (USDT-M) with proper logging and error handling.

---

## Project Structure

```
trading_bot_app/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (signing, sending, error surfacing)
│   ├── orders.py          # Order placement logic (MARKET, LIMIT, STOP_MARKET)
│   ├── validators.py      # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py  # Shared logger — file + console handlers
├── logs/                  # Auto-created; one log file per calendar day
├── cli.py                 # argparse CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Get Testnet Credentials

1. Go to <https://testnet.binancefuture.com>
2. Log in (GitHub OAuth is supported)
3. Navigate to **API Management** → generate a key pair
4. Copy the **API Key** and **Secret Key**

### 2. Install Dependencies

```bash
cd trading_bot_app
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Set Credentials

**Option A — environment variables (recommended)**

```bash
# Windows PowerShell
$env:BINANCE_API_KEY    = "your_key"
$env:BINANCE_API_SECRET = "your_secret"

# macOS / Linux
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
```

**Option B — pass inline on every command**

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET ...
```

---

## How to Run

### Market Order

```bash
# BUY 0.001 BTC at market price
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# SELL 0.01 ETH at market price
python cli.py --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Limit Order

```bash
# BUY 0.001 BTC with a limit price of 60000 USDT
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 60000

# SELL 0.001 BTC at 100000 USDT (GTC by default)
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

# IOC time-in-force
python cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 60000 --tif IOC
```

### Stop-Market Order (Bonus)

```bash
# Trigger a SELL if price drops to 55000
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 55000
```

---

## Sample Output

```
==================================================
  ORDER REQUEST SUMMARY
==================================================
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
==================================================

==================================================
  ORDER RESPONSE
==================================================
  Order ID     : 3847291023
  Client OID   : abc123xyz
  Symbol       : BTCUSDT
  Status       : FILLED
  Side         : BUY
  Type         : MARKET
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 67432.10
  Time         : 1714000000000
==================================================

  ✓ Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_YYYY-MM-DD.log`.

- **DEBUG** level in the file — full request params and raw responses
- **INFO** level on the console — order lifecycle events
- **ERROR** level — API errors and network failures

Log entries use the format:
```
2024-04-25 14:32:01 | INFO     | orders | Placing MARKET BUY order | symbol=BTCUSDT qty=0.001
2024-04-25 14:32:02 | INFO     | orders | MARKET order placed | orderId=3847291023 status=FILLED executedQty=0.001
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing credentials | Prints clear message, exits with code 1 |
| Invalid symbol / side / type | `ValidationError` printed, exits with code 1 |
| Non-positive quantity or price | `ValidationError` printed, exits with code 1 |
| LIMIT order without `--price` | Caught before API call, exits with code 1 |
| STOP_MARKET without `--stop-price` | Caught before API call, exits with code 1 |
| Binance API error (e.g. -1121) | `BinanceAPIError` logged and printed, exits with code 1 |
| Network / timeout failure | Logged and printed, exits with code 1 |

---

## Assumptions

- Only USDT-M perpetual futures are targeted (testnet endpoint `/fapi/v1/order`).
- Quantity and price precision must match the symbol's rules on the testnet;
  if Binance rejects with `-1111` (precision error), adjust your values accordingly.
- Credentials are never logged — only non-sensitive parameter keys appear in DEBUG logs.
- The `STOP_MARKET` type is used as the bonus third order type (no second price leg needed,
  making it straightforward to test on testnet without open positions).

---

## Running Tests (manual)

Use the sample commands above against the testnet.
The testnet resets periodically, so balances and open orders may disappear between sessions.
