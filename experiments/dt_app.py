import socket
import threading

import paho.mqtt.client as mqtt

import common


sock = socket.create_connection((common.PE_HOST, common.SOCKET_PORT))
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # send each message immediately


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(common.TOPIC, qos=common.QOS)


def on_message(client, userdata, msg):
    sock.sendall(msg.payload + b"\n")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="dt-app")
client.on_connect = on_connect
client.on_message = on_message

port = common.MQTT_PORT

common.connect(client, port)

print(f"forwarding {common.TOPIC} to {common.PE_HOST}:{common.SOCKET_PORT} (Ctrl+C to stop)")
threading.Event().wait()
