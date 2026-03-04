import asyncio

class Sensor:
    def __init__(self, id, topics, sync_rate):
        self.id = id
        self.topics = topics
        self.sync_rate = sync_rate
        self.get_sensor_data = None

    def get_sensor_data(self):
        if not self.get_sensor_data:
            raise NotImplementedError("get_sensor_data not implemented")
        return self.get_sensor_data()

    async def publish_data(self, client, qos):
        while True:
            data = self.get_sensor_data()
            for topic in self.topics["data"]:
                await client.publish(topic, data, qos)
            await asyncio.sleep(self.sync_rate)