from threading import Lock
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
from .bots.alpaca import AlpacaTradeBot, AlpacaDataBot, AlpacaRealTimeBot
from .db import get_db
from . import socketio

bp = Blueprint('alpaca', __name__, url_prefix='/alpaca')
thread = None
thread_lock = Lock()

conns = {}

tradeBot = AlpacaTradeBot()
@bp.route('/account', methods=["GET"])
def get_account():
    account = tradeBot.get_account()
    return jsonify(account)

@bp.route('/assets/<type>', methods=["GET"])
def get_all_assets(type):
    assets = tradeBot.get_all_assets(type)
    return assets

@bp.route('/assets/<id_or_symbol>', methods=["GET"])
def get_asset(id_or_symbol):
    asset = tradeBot.get_asset(id_or_symbol)
    return asset

@bp.route('/orders', methods=["POST"])
def get_orders():
    orders = tradeBot.get_orders(request.form)
    return orders

@bp.route('/orders/cancel/<id>', methods=["GET"])
def cancel_order(id):
    if id == "all":
        cancel_status = tradeBot.cancel_all_orders()
    else:
        cancel_status = tradeBot.cancel_order(id)
    return cancel_status

@bp.route('/orders/make/<side>', methods=["POST"])
def make_order(side):
    qty = request.form["qty"]
    symbol = request.form["symbol"]
    o = tradeBot.make_order(symbol, qty, side)
    print(o)
    order = { "symbol": o.symbol, "qty": o. qty, "side": o.side, "filled_avg_price": o.filled_avg_price }
    return order

@bp.route('/ws/start', methods=["GET"])
def start_ws():
    symbol = request.args.get("symbol")
    liveBot = AlpacaRealTimeBot("us_equity")
    conns[symbol] = liveBot
    liveBot.subscribe(symbol)
    return "started"

@socketio.on('connect')
def connect():
    print("Connected")
    print(request.sid)
    socketio.emit('status', {'msg': 'Connected'})

@socketio.on('subscribe')
def subscribe(msg):
    print(msg)
    print(request.sid)
    type = msg['type']
    symbols = msg['symbols']

    if type == 'us_equity' or type == 'crypto':
        liveBot = AlpacaRealTimeBot(type)
    else:
        emit('error', {'data': 'Invalid type'})
        return
    conns[request.sid] = liveBot

    liveBot.subscribe(symbols)

    # def background_thread():
    #     liveBot.subscribe(symbols)
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)


    # bot = AlpacaDataBot(type=type)
    # def background_thread():
    #     while True:
    #         socketio.sleep(1)
    #         socketio.emit('data', bot.get_latest_quote(symbol_or_symbols=symbols).json())
    # global thread
    # with thread_lock:
    #     if thread is None:
    #         thread = socketio.start_background_task(background_thread)


@socketio.on('disconnect')
def disconnect():
    print("Client disconnected")
    socketio.emit('status', { 'msg': 'Client disconnected' })

