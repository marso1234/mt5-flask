from flask import Flask, request, jsonify
from datetime import datetime
import time
# import the package
from mt5linux import MetaTrader5

# connecto to the server
mt5 = MetaTrader5(
    # host = 'localhost' (default)
    # port = 18812       (default)
) 

app = Flask(__name__)
trade_map = {}  # trade_id -> ticket

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
    info = mt5.symbol_info(symbol)
    return jsonify(info._asdict() if info else {'error': 'Symbol not found'})

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
    volume = data.get('volume')
    order_type = data.get('type', 'buy')
    trade_id = data.get('trade_id')

    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if order_type == 'buy' else tick.bid
    order_type_enum = mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL

    request_data = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_enum,
        "price": price,
        "deviation": 10,
        "magic": 234000,
        "comment": f"n8n automation {trade_id}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request_data)
    if result.retcode == mt5.TRADE_RETCODE_DONE and trade_id:
        trade_map[trade_id] = result.order

    return jsonify({'result': result._asdict()})

@app.route('/end_order', methods=['POST'])
def end_order():
    data = request.json
    trade_id = data.get('trade_id')
    ticket = data.get('ticket')

    success, msg = initialize_mt5()
    if not success:
        return jsonify({'error': msg}), 500

    if trade_id:
        ticket = trade_map.get(trade_id)
        if not ticket:
            return jsonify({'error': 'Trade ID not found'}), 404

    order = mt5.order_get(ticket=ticket)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    tick = mt5.symbol_info_tick(order.symbol)
    price = tick.bid if order.type == mt5.ORDER_TYPE_BUY else tick.ask
    close_type = mt5.ORDER_TYPE_SELL if order.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": order.symbol,
        "volume": order.volume_current,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": 10,
        "magic": 234000,
        "comment": f"n8n close {trade_id or ticket}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
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
