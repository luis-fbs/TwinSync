import base64
import json
import threading
import time

import websocket
import paho.mqtt.client as mqtt
from flask import Flask, render_template, Response

import config as cfg


SUBSCRIBE = (
    "START-SEND-EVENTS"
    f"?namespaces={cfg.NAMESPACE}"
    f"&filter=and(eq(thingId,'{cfg.THING_ID}'),like(resource:path,'/features'))"
)

angle = 90.0
is_safe = True
changed = threading.Condition()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(cfg.MQTT_HOST, cfg.MQTT_PORT)
client.loop_start()


def update_safe(value):
    global is_safe

    if value == is_safe:
        return

    is_safe = value
    client.publish(cfg.MQTT_COMMAND_TOPIC, json.dumps({"safe": is_safe}))
    print(f"safe = {is_safe}")


def on_ditto_open(ws):
    print("Connected to Ditto")
    ws.send(SUBSCRIBE)


def on_ditto_message(ws, message):
    current_time = time.time()
    global angle

    if message == "START-SEND-EVENTS:ACK":
        print(f"Subscribed to {cfg.THING_ID} / feature 'angle'")
        return

    event = json.loads(message)
    value = event["value"]

    if "angle" not in value:
        return

    with changed:
        angle = value["angle"]["properties"]["value"]
        timestamp = value["timestamp"]["properties"]["value"]
        update_safe(current_time - timestamp <= cfg.MAX_OFFSET)
        changed.notify_all()


def on_ditto_error(ws, error):
    print("Error:", error)


def on_ditto_close(ws, status, msg):
    print("Ditto connection closed")


def listen_to_ditto():
    token = base64.b64encode(f"{cfg.DITTO_AUTH[0]}:{cfg.DITTO_AUTH[1]}".encode()).decode()
    ws = websocket.WebSocketApp(
        cfg.DITTO_WS,
        header=[f"Authorization: Basic {token}"],
        on_open=on_ditto_open,
        on_message=on_ditto_message,
        on_error=on_ditto_error,
        on_close=on_ditto_close,
    )
    ws.run_forever(ping_interval=30)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", thing_id=cfg.THING_ID)


@app.route("/stream")
def stream():
    def events():
        yield f"data: {json.dumps({'angle': angle, 'safe': is_safe})}\n\n"
        while True:
            with changed:
                updated = changed.wait(timeout=15)
                data = {'angle': angle, 'safe': is_safe}
            yield f"data: {json.dumps(data)}\n\n" if updated else ": ping\n\n"

    return Response(events(), mimetype="text/event-stream")


threading.Thread(target=listen_to_ditto, daemon=True).start()

if __name__ == "__main__":
    app.run(host= '0.0.0.0', port=5000, threaded=True)
