#!/usr/bin/env python3

import requests
import socket
import ST7735
import time
import datetime
import json
from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError, ChecksumMismatchError
from enviroplus import gas
from subprocess import PIPE, Popen, check_output
from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont

try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559

    ltr559 = LTR559()
except ImportError:
    import ltr559

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

bus = SMBus(1)

# Create BME280 instance
bme280 = BME280(i2c_dev=bus)

# Create LCD instance
disp = ST7735.ST7735(
    port=0,
    cs=1,
    dc=9,
    backlight=12,
    rotation=270,
    spi_speed_hz=10000000
)

# Initialize display
disp.begin()

# Create PMS5003 instance
pms5003 = PMS5003()

# Compensation factor for temperature
comp_factor = 2.25

# Read values from BME280 and PMS5003 and return as dict
def read_values():
    values = {}
    cpu_temp = get_cpu_temperature()
    raw_temp = bme280.get_temperature()
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
    values["name"] = get_serial_number() #"raspi-1"
    values["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    values["temp"] = "{:.2f}".format(comp_temp)
    values["pressure"] = "{:.2f}".format(bme280.get_pressure() * 100)
    values["humidity"] = "{:.2f}".format(bme280.get_humidity())
    values["light"] = "{:.2f}".format(ltr559.get_lux())
    values["proximity"] = "{:.2f}".format(ltr559.get_proximity())
    raw_gas = gas.read_all()
    values["oxidised"] = "{:.2f}".format(raw_gas.oxidising / 1000)
    values["reduced"] = "{:.2f}".format(raw_gas.reducing / 1000)
    values["nh3"] = "{:.2f}".format(raw_gas.nh3 / 1000)
    try:
        pm_values = pms5003.read()
        values["pm25"] = str(pm_values.pm_ug_per_m3(2.5))
        values["pm10"] = str(pm_values.pm_ug_per_m3(10))
        values["pm1"] = str(pm_values.pm_ug_per_m3(1))
    except(ReadTimeoutError, ChecksumMismatchError):
        logging.info("Failed to read PMS5003. Reseting and retrying.")
        pms5003.reset()
        pm_values = pms5003.read()
        values["pm25"] = str(pm_values.pm_ug_per_m3(2.5))
        values["pm10"] = str(pm_values.pm_ug_per_m3(10))
        values["pm1"] = str(pm_values.pm_ug_per_m3(1))
    return values


# Get CPU temperature to use for compensation
def get_cpu_temperature():
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                return line.split(":")[1].strip()


# Check for Wi-Fi connection
def check_wifi():
    if check_output(['hostname', '-I']):
        return True
    else:
        return False

# Display Raspberry Pi serial and Wi-Fi status on LCD
def display_status():
    wifi_status = "connected" if check_wifi() else "disconnected"
    text_colour = (255, 255, 255)
    back_colour = (141, 211, 95) if check_wifi() else (255, 85, 85)
    id = get_serial_number()
    message = "{}\nWi-Fi: {}".format(id, wifi_status)
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    size_x, size_y = draw.textsize(message, font)
    x = (WIDTH - size_x) / 2
    y = (HEIGHT / 2) - (size_y / 2)
    draw.rectangle((0, 0, 160, 80), back_colour)
    draw.text((x, y), message, font=font, fill=text_colour)
    disp.display(img)

class Client():
   def __init__(self, url="https://ke-ap01.econ.muni.cz/pushToDB.php"):
      self.url = url

   def send_data(self):
      data = read_values()
      requests.post(self.url, data)

c = Client()
while True:
    display_status()
    c.send_data()
