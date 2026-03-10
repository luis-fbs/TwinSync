from gpiozero import LED

from Sensors.sensor import *


class LEDSensor(Sensor):
    def __init__(self, id, topic, feature_path, sync_rate, gpio):
        super().__init__(id, topic, feature_path, sync_rate)
        self.led = LED(gpio)

    def get_sensor_data(self):
        return "On" if self.led.is_lit else "Off"
