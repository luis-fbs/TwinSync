import json

import paho.mqtt.client as mqtt

import common

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pe-mqtt-tls")
client.tls_set(ca_certs=common.CA_CERT)
common.connect(client, common.TLS_PORT)


def send(message):
    client.publish(common.TOPIC, json.dumps(message), qos=common.QOS)


common.send_messages(send)
client.disconnect()
client.loop_stop()
