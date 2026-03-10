from gpiozero import Buzzer

from Sensors.sensor import *


class BuzzerSensor(Sensor):
    def __init__(self, id, topic, feature_path,sync_rate, gpio):
        super().__init__(id, topic, feature_path, sync_rate)
        self.buzzer = Buzzer(gpio)


    def get_sensor_data(self):
       return "On" if self.buzzer.is_active else "Off"
