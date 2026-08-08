import base64
import json
import threading
import time

import websocket
from flask import Flask, render_template, Response

import config as cfg


SUBSCRIBE = (
    "START-SEND-EVENTS"
    f"?namespaces={cfg.NAMESPACE}"
    f"&filter=and(eq(thingId,'{cfg.THING_ID}'),like(resource:path,'/features'))"
)

angle = 90.0
timestamp = time.time()
changed = threading.Condition()

app = Flask(__name__)

def on_open(ws):
    print("Connected to Ditto")
    ws.send(SUBSCRIBE)


def on_message(ws, message):
    current_time = time.time()
    global angle, timestamp

    if message == "START-SEND-EVENTS:ACK":
        print(f"Subscribed to {cfg.THING_ID} / feature 'angle'")
        return

    event = json.loads(message)
    value = event["value"]
    angle = value["angle"]["properties"]["value"]
    timestamp = value["timestamp"]["properties"]["value"]

    #ToDo: change safe if time difference is not acceptable

    with changed:
        changed.notify_all()


def on_error(ws, error):
    print("Error:", error)


def on_close(ws, status, msg):
    print("Ditto connection closed")


def listen_to_ditto():
    token = base64.b64encode(f"{cfg.DITTO_AUTH[0]}:{cfg.DITTO_AUTH[1]}".encode()).decode()
    ws = websocket.WebSocketApp(
        cfg.DITTO_WS,
        header=[f"Authorization: Basic {token}"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(ping_interval=30)


@app.route("/")
def index():
    return render_template("index.html", thing_id=cfg.THING_ID)


@app.route("/stream")
def stream():
    def events():
        yield f"data: {angle}\n\n"
        while True:
            with changed:
                updated = changed.wait(timeout=15)
                data = {'angle': angle, 'safe': True}
            yield f"data: {json.dumps(data)}\n\n" if updated else ": ping\n\n"

    return Response(events(), mimetype="text/event-stream")


threading.Thread(target=listen_to_ditto, daemon=True).start()

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=5000, threaded=True)
