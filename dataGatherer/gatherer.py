from sense_hat import SenseHat
import os
import time
import re


class Gatherer:
    """
    This class will gather data from various sensors of the SenseHat and other various sources from the RaspberryPi.
    The data is mostly related to temperature and the RasberryPi CPU usage.
    """

    def __init__(self, target_temperature, time_interval, log_filename):
        self.target_temperature = target_temperature
        self.time_interval = time_interval
        self.log_filename = log_filename

        self.sense_hat = SenseHat()
        self.current_cpu_times = None
        self.previous_cpu_times = None

        # We'll need to update the cpu stats once and sleep the time_interval for the first run.
        self.update_cpu_times()
        time.sleep(self.time_interval)

        self.main_loop()

    def main_loop(self):
        """
        The main loop will gather various data from the sensors of the SensorHat and the RaspberryPi and log it all
        to a file.
        :return:
        """
        while True:
            self.update_cpu_times()

            time.sleep(self.time_interval)

#   def get_all_data(self):

    def get_cpu_temp(self):
        """
        This get the CPU temperature from "/opt/vc/bin/vcgencmd measure_temp".
        :return: A float containing the CPU temperature in Celsius.
        """
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

    def get_cpu_usage(self):
        """
        This calculte the current CPU usage.
        :return: Return the CPU usage in the same style as the load average is shown by uptime on Linux (i.e. 0.52
        for 52% utilization of one CPU core).
        """
        delta_cpu_stats = self.get_delta_cpu_times()
        cpu_usage_in_percent = 100 - (delta_cpu_stats[len(delta_cpu_stats) - 1] * 100.0 / sum(delta_cpu_stats))
        # Calculate the CPU usage in the same format as the load average
        cpu_usage_in_cpu_core = cpu_usage_in_percent / 100 * 4

        return cpu_usage_in_cpu_core

    def get_delta_cpu_times(self):
        """
        This calculate the difference between the current cpu times and the previous cpu times that were last updated
        roughly since the time_interval in seconds. The cpu times are gathered with update_cpu_times().
        :return: A list that contains the difference between the current cpu times and the previous cpu times.
        """
        delta_cpu_stats = []
        for i in range(len(self.previous_cpu_times)):
            delta_cpu_stats[i] = self.current_cpu_times[i] - self.previous_cpu_times[i]

        return delta_cpu_stats

    def update_cpu_times(self):
        """
        This will move the current_cpu_times into the previous_cpu_times and update the current_cpu_times from
        /proc/stat.
        """
        self.previous_cpu_times = self.current_cpu_times

        cpu_stat_file = open('/proc/stat', 'r')
        cpu_times = cpu_stat_file.readline().split(" ")[2:6]
        cpu_stat_file.close()

        for i in range(len(cpu_times)):
            cpu_times[i] = int(cpu_times[i])

        self.current_cpu_times = cpu_times



