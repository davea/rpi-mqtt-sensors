#!/usr/bin/env python3
from time import sleep
from socket import gethostname

from w1thermsensor import W1ThermSensor
import paho.mqtt.publish as publish

BROKER="10.0.1.216"
TOPIC="sensor/temperature/{}".format(gethostname())
DELAY=10

def main():
    sensor = W1ThermSensor()
    while True:
        temperature = sensor.get_temperature()
        print("Temperature: {}".format(temperature))
        publish.single(TOPIC, str(temperature), hostname=BROKER)
        print("Sleeping for {} seconds...".format(DELAY))
        sleep(DELAY)

if __name__ == '__main__':
    main()