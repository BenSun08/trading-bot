# Back-end

## How to run

run the http web server

```sh
flask run
```

run the Socket.io server

```sh
gunicorn -k gevent -w 1 app:app
```
