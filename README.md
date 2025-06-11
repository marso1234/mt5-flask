# MT5 Linux Setup

MT5 python library supports Windows natively, linux os requires additional setup:

1. Setup wine

2. Install Meta Trader and Python 3.8

3. Install MT5 and Flask package

4. Commands may refer to setup_MT5_ubuntu.sh

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
