from flask import Flask, request, jsonify
from datetime import datetime
import MetaTrader5 as mt5
import time
# import the package

app = Flask(__name__)
epsilon = 1e-7 # A very small value to prevent value being identified as integer (which cause error in MT5)
def initialize_mt5():
    if not mt5.initialize():
        return False, mt5.last_error()
    return True, "MT5 initialized"

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'API and MT5 are running'})

@app.route('/check_balance', methods=['GET'])
def check_balance():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    info = mt5.account_info()
    return jsonify({
        'balance': info.balance,
        'equity': info.equity,
        'margin': info.margin,
        'free_margin': info.margin_free
    })

@app.route('/account_info', methods=['GET'])
def account_info():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    info = mt5.account_info()
    return jsonify(info._asdict())

@app.route('/current_orders', methods=['GET'])
def current_orders():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    orders = mt5.orders_get()
    return jsonify([o._asdict() for o in orders] if orders else [])

@app.route('/positions', methods=['GET'])
def positions():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    positions = mt5.positions_get()
    return jsonify([p._asdict() for p in positions] if positions else [])

@app.route('/symbol_info', methods=['GET'])
def symbol_info():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'Missing symbol parameter'}), 400
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    # Automatically add symbol to Market Watch if not already present
    if not mt5.symbol_select(symbol, True):
        return jsonify({'error': f'Failed to add symbol {symbol} to Market Watch'}), 500

    info = mt5.symbol_info(symbol)
    info = info._asdict() if info else None
    if info is not None:
        trail = 0
        # Retry a few times if price is invalid
        while info.get("ask", 0) == 0 and trail < 5:
            time.sleep(1)
            info = mt5.symbol_info(symbol)._asdict()
            
    # Remove from Market Watch
    mt5.symbol_select(symbol, False)
    
    return jsonify(info if info else {'error': 'Symbol not found'})

@app.route('/order_history', methods=['GET'])
def order_history():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    from_dt = datetime.strptime(from_date, '%Y-%m-%d') if from_date else datetime.now().replace(hour=0, minute=0)
    to_dt = datetime.strptime(to_date, '%Y-%m-%d') if to_date else datetime.now()
    history = mt5.history_deals_get(from_dt, to_dt)
    return jsonify([h._asdict() for h in history] if history else [])

@app.route('/start_order', methods=['POST'])
def start_order():
    data = request.json
    symbol = data.get('symbol')
    size = data.get('size')
    order_type = data.get('order_type').upper()
    strategy = data.get('strategy')
    stop_loss = data.get('stop_loss')
    stop_profit = data.get('stop_profit')
    filling_mode = data.get('filling_mode')

    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == 'BUY' else tick.bid
    order_type_enum = mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL
    
    request_data = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": size + epsilon - epsilon,
        "type": order_type_enum,
        "price": price + epsilon - epsilon,
        "deviation": 10,
        "magic": 234000,
        "comment": strategy,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode - 1, # Offset of data?
        'sl': stop_loss + epsilon - epsilon,
        'tp': stop_profit + epsilon - epsilon
    }

    print(request_data)
    print(f"Order is {order_type}, {order_type=='BUY'}")
    
    result = mt5.order_send(request_data)

    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Order send failed:", mt5.last_error())
        return jsonify({'error': mt5.last_error()})
        
    return jsonify({'result': result._asdict()})

@app.route('/end_order', methods=['POST'])
def end_order():
    data = request.json
    symbol = data.get('symbol')
    entry_action = data.get('entry_action')
    entry_volume = data.get('volume')
    filling_mode = data.get('filling_mode')
    ticket = data.get('ticket')

    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    tick = mt5.symbol_info_tick(symbol)
    price = tick.bid if entry_action == mt5.ORDER_TYPE_BUY else tick.ask
    close_type = mt5.ORDER_TYPE_SELL if entry_action == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": entry_volume + epsilon - epsilon,
        "type": close_type,
        "position": ticket,
        "price": price + epsilon - epsilon,
        "deviation": 10,
        "magic": 234000,
        "comment": f"Signal Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode - 1,
    }

    result = mt5.order_send(close_request)
    return jsonify({'result': result._asdict()})

@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    data = request.json
    ticket = data.get('ticket')
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    order = mt5.order_get(ticket=ticket)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    cancel_request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": ticket
    }

    result = mt5.order_send(cancel_request)
    return jsonify({'result': result._asdict()})

@app.route('/close_all', methods=['POST'])
def close_all():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    positions = mt5.positions_get()
    if not positions:
        return jsonify({'message': 'No open positions'})

    results = []
    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 234000,
            "comment": "n8n close all",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(close_request)
        results.append(result._asdict())

    return jsonify({'closed_positions': results})

@app.route('/clear_all_watches', methods=['POST'])
def clear_all_watches():
    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    # Get all symbols that are currently selected (visible in Market Watch)
    all_symbols = mt5.symbols_get()

    removed = []
    failed = []

    for symbol_info in all_symbols:
        symbol = symbol_info.name
        # Only try to remove if currently selected
        if mt5.symbol_info(symbol).visible:
            if mt5.symbol_select(symbol, False):
                removed.append(symbol)
            else:
                failed.append(symbol)

    return jsonify({
        'removed': removed,
        'failed': failed,
        'message': f'Removed {len(removed)} symbols from Market Watch.'
    })

@app.route('/webhook_log', methods=['POST'])
def webhook_log():
    data = request.json
    print(f"Webhook received: {data}")
    return jsonify({'status': 'logged', 'data': data})

if __name__ == '__main__':
    success, msg = initialize_mt5()
    if not success:
        print(msg)
    else:
      app.run(debug=True)
