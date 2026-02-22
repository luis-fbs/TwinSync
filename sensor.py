class Sensor:
    def __init__(self, id, sync_rate):
        self.id = id
        self.sync_rate = sync_rate
        self.get_sensor_data = None

    def get_sensor_data(self):
        if not self.get_sensor_data:
            raise NotImplementedError("get_sensor_data not implemented")
        return self.get_sensor_data()