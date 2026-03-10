from gpiozero import DistanceSensor

from Sensors.sensor import *


class UltrasonicSensor(Sensor):
    def __init__(self, id, topic, feature_path, sync_rate, echo, trigger):
        super().__init__(id, topic, feature_path, sync_rate)
        self.ultrasonic = DistanceSensor(echo=echo, trigger=trigger)

    def get_sensor_data(self):
        return 100 * self.ultrasonic.distance
