import asyncio
import json


class Sensor:
    def __init__(self, id, topic, feature_path, sync_rate):
        self.feature_path = feature_path
        self.id = id
        self.topic = topic
        self.sync_rate = sync_rate

    def get_sensor_data(self):
        raise NotImplementedError("get_sensor_data not implemented")

    def ditto_payload(self):
        return {
            "topic": self.topic,
            "headers": {},
            "path": self.feature_path,
            "value": self.get_sensor_data(),
        }

    async def publish_data(self, client, qos, topic):
        while True:
            await client.publish(topic, payload=json.dumps(self.ditto_payload()), qos=qos)
            await asyncio.sleep(self.sync_rate)