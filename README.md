# Linux Support

1. Install Wine.

2. Install Python for Windows on Linux with the help of Wine.

3. Find the path to python.exe.

4. Install mt5 library on your Windows Python version.

5. On a terminal:
   `python -m mt5linux <path/to/python.exe>`

# 📘 MT5 - Flask API - Function Summary

## 1. `/ping`
Checks if the API and MT5 terminal are running and responsive.

## 2. `/check_balance`
Returns key account metrics including balance, equity, margin, and free margin.

## 3. `/account_info`
Provides detailed account information such as login ID, leverage, and server.

## 4. `/current_orders`
Retrieves all current pending orders that have not yet been executed.

## 5. `/positions`
Lists all currently open positions in the trading account.

## 6. `/symbol_info`
Returns metadata for a specific trading symbol, such as spread and tick size.

## 7. `/order_history`
Fetches historical closed orders or deals within a specified date range.

## 8. `/start_order`
Places a new market order (buy or sell) with optional trade ID tracking.

## 9. `/end_order`
Closes an existing order using either a ticket number or a previously assigned trade ID.

## 10. `/cancel_order`
Cancels a pending order by its ticket number before it is executed.

## 11. `/close_all`
Closes all currently open positions in the account.

## 12. `/webhook_log`
Logs incoming webhook payloads for debugging or audit purposes.
