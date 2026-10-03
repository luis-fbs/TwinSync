import json

import paho.mqtt.client as mqtt

import common

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pe-mqtt")
common.connect(client, common.MQTT_PORT)


def send(message):
    client.publish(common.TOPIC, json.dumps(message), qos=common.QOS)


common.send_messages(send)
client.disconnect()
client.loop_stop()
