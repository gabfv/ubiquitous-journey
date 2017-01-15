from sense_hat import SenseHat
import os
import time
import re

class Gatherer:
    """
    This class will gather data from various sensors of the SenseHat and other various sources from the RaspberryPi.
    The date is mostly related to temperature and the RasberryPi CPU usage.
    """

    def __init__(self, target_temperature, time_interval, log_filename):
        self.target_temperature = target_temperature
        self.time_interval = time_interval
        self.log_filename = log_filename
        self.sense_hat = SenseHat()

    def main_loop(self):
        while True:

            time.sleep(self.time_interval)

#   def get_all_data(self):

    def get_cpu_temp(self):
        os_command = os.popen('/opt/vc/bin/vcgencmd measure_temp')
        command_result = os_command.read()
        match = re.search('^temp=([^\']+)\'C$', command_result)
        cpu_temp = float(match.group(1))
        return cpu_temp

    def get_sense_hat_temp(self):
        return self.sense_hat.get_temperature()

    def get_sense_hat_temp_from_pressure(self):
        return self.sense_hat.get_temperature_from_pressure()

    def get_sense_hat_temp_from_humidity(self):
        return self.sense_hat.get_temperature_from_humidity()