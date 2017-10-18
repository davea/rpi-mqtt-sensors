#!/usr/bin/env python3
from time import sleep
from socket import gethostname
from configparser import ConfigParser
from os.path import expanduser

from w1thermsensor import W1ThermSensor
import bme680

import paho.mqtt.publish as publish

config = ConfigParser()
config.read(expanduser("~/.config/homesense/temperature.ini"))


class BaseSensor:
    id = None

    def topic_for_attribute(self, attribute):
        return config['mqtt']['topic_format'].format(attribute=attribute, id=self.id)

    @property
    def topics_and_values(self):
        return []


class W1Sensor(BaseSensor):
    @classmethod
    def create_sensors(cls):
        # sensors = W1ThermSensor.get_available_sensors()
            # sensor_topics = list(zip(sensors, get_sensor_topics(sensors)))

        return []


class BME680Sensor(BaseSensor):
    _sensor = None

    def __init__(self, id, i2c_addr=None):
        self.id = id
        if i2c_addr:
            self._sensor = bme680.BME680(i2c_addr=i2c_addr)
        else:
            self._sensor = bme680.BME680()

        self._sensor.set_humidity_oversample(bme680.OS_8X)
        self._sensor.set_pressure_oversample(bme680.OS_8X)
        self._sensor.set_temperature_oversample(bme680.OS_8X)
        self._sensor.set_filter(bme680.FILTER_SIZE_3)

    @property
    def topics_and_values(self):
        if self._sensor.get_sensor_data():
            return [
                (self.topic_for_attribute('temperature'), self._sensor.data.temperature),
                (self.topic_for_attribute('humidity'), self._sensor.data.humidity),
                (self.topic_for_attribute('pressure'), self._sensor.data.pressure),
            ]
        else:
            return []

    @classmethod
    def create_sensors(cls):
        sensors = []

        # Create sensors based on what's in the ini file
        for i2c_addr, mqtt_id in config['bme680sensors'].items():
            sensors.append(cls(mqtt_id, int(i2c_addr, 16)))

        # If there's nothing in the ini file, then create one sensor
        # with the default i2c address and mqtt id from the hostname
        if not sensors:
            sensors.append(cls(gethostname()))

        return sensors


def get_sensor_topics(sensors, configkey):
    for sensor in sensors:
        if len(sensors) == 1:
            suffix = config['w1sensors'].get(sensor.id, gethostname())
        else:
            suffix = config['w1sensors'].get(sensor.id, "{}_{}".format(gethostname(), sensor.id))
        yield "{}{}".format(config['mqtt']['topic_prefix'], suffix)


def main():
    sensors = []
    sensors.extend(BME680Sensor.create_sensors())
    sensors.extend(W1Sensor.create_sensors())

    if len(sensors) == 0:
        raise Exception("No sensors found.")
    while True:
        messages = []
        for sensor in sensors:
            for topic, payload in sensor.topics_and_values:
                messages.append({'topic': topic, 'payload': str(payload)})
        if messages:
            publish.multiple(messages, hostname=config['mqtt']['broker'])
        else:
            print("No messages to publish, bit weird.")
        sleep(int(config['general']['delay']))

if __name__ == '__main__':
    main()
