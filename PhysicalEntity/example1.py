import asyncio
import os

from aiomqtt import Client

from Sensors.buzzersensor import BuzzerSensor
from Sensors.ledsensor import LEDSensor
from Sensors.ultrasonicsensor import UltrasonicSensor


BROKER = os.environ['BROKER']
PORT = int(os.environ['PORT'])
USERNAME = os.environ['USERNAME']
PASSWORD = os.environ['PASSWORD']
TOPIC = os.environ['TOPIC']

async def main():
    led = LEDSensor(1, "room/alerts/things/twin/commands/modify", "/features/led/properties/status", 1, 23 )
    buzzer = BuzzerSensor(2, "room/alerts/things/twin/commands/modify", "/features/buzzer/properties/status",  0.5, 18)
    ultrasonicSensor = UltrasonicSensor(3, "room/distanceController/things/twin/commands/modify", "/features/distance/properties/value", 0.3, 27, 17)

    sensors = [led, buzzer, ultrasonicSensor]

    async with Client(BROKER, PORT, username=USERNAME, password=PASSWORD) as client:
        tasks = [
            asyncio.create_task(sensor.publish_data(client, 1, TOPIC))
            for sensor in sensors
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())