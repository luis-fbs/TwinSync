import json
import config as cfg

from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo, Button
from time import sleep, time
import paho.mqtt.client as mqtt


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(cfg.MQTT_HOST, cfg.MQTT_PORT, 60)
client.loop_start()

factory = PiGPIOFactory()

servo = AngularServo(
    18,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0005,
    max_pulse_width=0.0024,
    pin_factory=factory,
)

right_button = Button(27, pin_factory=factory)
left_button = Button(22, pin_factory=factory)

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
    client.loop_stop()
    client.disconnect()
