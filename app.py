from main import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, port=5000)
    # from gevent import pywsgi
    # from geventwebsocket.handler import WebSocketHandler
    # server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    # server.serve_forever()