import json
import threading

import config as cfg

from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo, Button, LED
from time import sleep, time
import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(cfg.MQTT_HOST, cfg.MQTT_PORT, 60)
client.loop_start()

factory = PiGPIOFactory()

servo = AngularServo(
    cfg.SERVO_GPIO,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0005,
    max_pulse_width=0.0024,
    pin_factory=factory,
)

right_button = Button(cfg.RIGHT_BUTTON_GPIO, pin_factory=factory)
left_button = Button(cfg.LEFT_BUTTON_GPIO, pin_factory=factory)
led = LED(cfg.LED_GPIO, pin_factory=factory)


def on_command(client, userdata, message):
    command = json.loads(message.payload.decode("utf-8"))

    if command["safe"]:
        led.off()
    else:
        led.on()


def listen_to_commands():
    command_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    command_client.on_message = on_command
    command_client.connect(cfg.MQTT_HOST, cfg.MQTT_PORT, 60)
    command_client.subscribe(cfg.MQTT_COMMAND_TOPIC)
    command_client.loop_forever()


threading.Thread(target=listen_to_commands, daemon=True).start()

angle = 90
servo.angle = angle

last_published = None
last_publish_time = 0.0

def publish(value):
    global last_published, last_publish_time

    time_ = time()

    payload = {
        "topic": f"{cfg.NAMESPACE}/{cfg.THING_NAME}/things/twin/commands/modify",
        "headers": {},
        "path": "/features",
        "value": {
            "angle": {"properties": {"value": value}},
            "timestamp": {"properties": {"value": time_}}
        }
    }

    client.publish(cfg.MQTT_TOPIC, json.dumps(payload))
    last_published = value
    last_publish_time = time_

publish(angle)

try:
    while True:
        old_angle = angle
        moving = True

        if right_button.is_pressed:
            angle = max(0, angle - cfg.STEP)

        elif left_button.is_pressed:
            angle = min(180, angle + cfg.STEP)

        else:
            moving = False

        if angle != old_angle:
            servo.angle = angle

        if angle != last_published:
            if not moving or time() - last_publish_time >= cfg.PUBLISH_INTERVAL:
                publish(angle)

        sleep(cfg.SLEEP_TIME)

except KeyboardInterrupt:
    pass

finally:
    servo.detach()
    led.off()
    led.close()
    client.loop_stop()
    client.disconnect()
