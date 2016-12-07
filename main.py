#!/usr/bin/env python3
from time import sleep
from socket import gethostname
from configparser import ConfigParser
from os.path import expanduser

from w1thermsensor import W1ThermSensor
import paho.mqtt.publish as publish

config = ConfigParser()
config.read(expanduser("~/.config/homesense/temperature.ini"))

def get_sensor_topics(sensors):
    for sensor in sensors:
        if len(sensors) == 1:
            suffix = config['sensors'].get(sensor.id, gethostname())
        else:
            suffix = config['sensors'].get(sensor.id, "{}_{}".format(gethostname(), sensor.id))
        yield "{}{}".format(config['mqtt']['topic_prefix'], suffix)

def main():
    sensors = W1ThermSensor.get_available_sensors()
    if len(sensors) == 0:
        raise Exception("No sensors found.")
    sensor_topics = list(zip(sensors, get_sensor_topics(sensors)))
    while True:
        messages = []
        for sensor, topic in sensor_topics:
            temperature = sensor.get_temperature()
            print("Temperature of {}: {}".format(sensor.id, temperature))
            messages.append({'topic': topic, 'payload': str(temperature)})
            print(messages[-1])
        if messages:
            publish.multiple(messages, hostname=config['mqtt']['broker'])
        else:
            print("No messages to publish, bit weird.")
        print("Sleeping for {} seconds...".format(config['general']['delay']))
        sleep(int(config['general']['delay']))

if __name__ == '__main__':
    main()