import os
import re
import time
from datetime import datetime

from sense_hat import SenseHat


class Gatherer:
    """
    This class will gather data from various sensors of the SenseHat and other various sources from the RaspberryPi.
    The data is mostly related to temperature and the RaspberryPi CPU usage.
    """

    order_of_columns = ['date', 'cpu_divisor_for_target_temp', 'target_temperature', 'cpu_usage', 'load_avg_1_min',
                        'load_avg_5_min', 'load_avg_15_min', 'sense_hat_temp', 'sense_hat_temp_from_humidity',
                        'sense_hat_temp_from_pressure', 'cpu_temp', 'accelerometer_x', 'accelerometer_y',
                        'accelerometer_z']

    def __init__(self, queue_start_logging, polling_interval, log_filename, log_data_separator, target_temperature):
        """
        Init
        :param queue_start_logging: Contains the queue that will activate the logging.
        :param polling_interval: Contains the time the main loop sleep in seconds. Mainly affect the speed of logging.
        :param log_filename: Contains the filename of the logging file.
        :param log_data_separator: The separator for the values inside the logging file.
        :param target_temperature: An instance of TargetTemperature.
        """
        self.queue_start_logging = queue_start_logging
        self.target_temperature = target_temperature
        self.polling_interval = polling_interval
        self.log_filename = log_filename
        self.log_data_separator = log_data_separator

        self.sense_hat = SenseHat()
        self.file_handle_log = None
        self.current_cpu_times = None
        self.previous_cpu_times = None
        self.cpu_load_avg_1_min = None
        self.cpu_load_avg_5_min = None
        self.cpu_load_avg_15_min = None
        self.sense_hat_temp = None
        self.sense_hat_temp_from_humidity = None
        self.sense_hat_temp_from_pressure = None
        self.cpu_temp = None
        self.data_for_logging = {}

        if self.queue_start_logging:
            self.current_target_temperature = target_temperature.get_temperature()
            self.run()

    def start_logging_loop(self):
        """
        Open the file for logging and insert headers if necessary, then start the actual logging.
        """
        # TODO: should check if the header is correct. Perhaps include a version number?
        self.file_handle_log = self.open_log_file()
        self.insert_log_column_headers()

        self.logging_loop()

    def logging_loop(self):
        """
        The logging loop will gather various data from the sensors of the SensorHat and the RaspberryPi and log it all
        to a file.
        """
        # We'll need to update the cpu stats once and sleep the time_interval for the first run.
        self.update_cpu_stat_times()
        time.sleep(self.polling_interval)

        logging_active = True
        while logging_active:
            self.update_all_data_for_logging()
            self.log_all_data()
            time.sleep(self.polling_interval)

            # Check if logging is still active.
            if self.queue_start_logging.qsize() > 0:
                logging_active = self.queue_start_logging.get()

        self.close_log_file()

    def run(self):
        """
        This will simply wait until logging is active.
        """
        while True:
            if self.queue_start_logging.get():
                self.start_logging_loop()
            time.sleep(self.polling_interval)

    def open_log_file(self):
        """
        Open the log file.
        :return: File handle for the log file.
        """
        return open(self.log_filename, 'a+')  # TODO: Need an exception handler.

    def close_log_file(self):
        """
        Close the file handle for the log.
        """
        self.file_handle_log.close()

    def insert_log_column_headers(self):
        """
        Insert the column headers in the log file, if there ain't any.
        """
        if os.path.getsize(self.log_filename) == 0:
            self.file_handle_log.write(self.log_data_separator.join(Gatherer.order_of_columns) + '\n')

    def log_all_data(self):
        """
        Log (append) all the data that's captured into the logging file.
        """
        for column in Gatherer.order_of_columns:
            self.file_handle_log.write(self.data_for_logging[column])
            if column is not Gatherer.order_of_columns[-1]:
                self.file_handle_log.write(self.log_data_separator)

        self.file_handle_log.write('\n')

    def update_all_data_for_logging(self):
        """
        Update all data and "stringify" it for logging purposes.
        """
        self.update_cpu_stat_times()
        self.update_all_temp_data()
        self.update_cpu_load_average()
        accelerometer_data = self.get_accelerometer_data()

        # Related to what's needed to reach target temperature.
        self.data_for_logging['cpu_divisor_for_target_temp'] = str(self.calculate_cpu_divisor_for_target_temp())
        self.data_for_logging['target_temperature'] = str(self.current_target_temperature)

        # CPU usage and averages
        self.data_for_logging['cpu_usage'] = str(self.get_cpu_usage())
        self.data_for_logging['load_avg_1_min'] = str(self.cpu_load_avg_1_min)
        self.data_for_logging['load_avg_5_min'] = str(self.cpu_load_avg_5_min)
        self.data_for_logging['load_avg_15_min'] = str(self.cpu_load_avg_15_min)

        # Temperature
        self.data_for_logging['sense_hat_temp'] = str(self.sense_hat_temp)
        self.data_for_logging['sense_hat_temp_from_humidity'] = str(self.sense_hat_temp_from_humidity)
        self.data_for_logging['sense_hat_temp_from_pressure'] = str(self.sense_hat_temp_from_pressure)
        self.data_for_logging['cpu_temp'] = str(self.cpu_temp)

        # Accelerometer data
        self.data_for_logging['accelerometer_x'] = str(accelerometer_data['x'])
        self.data_for_logging['accelerometer_y'] = str(accelerometer_data['y'])
        self.data_for_logging['accelerometer_z'] = str(accelerometer_data['z'])

        # This should be added last so the date is when nearly everything is done before actual logging.
        self.data_for_logging['date'] = str(datetime.now())

    def update_all_temp_data(self):
        """
        Update all the data related to temperature.
        """
        self.update_cpu_temp()
        self.update_sense_hat_temp()
        self.update_sense_hat_temp_from_humidity()
        self.update_sense_hat_temp_from_pressure()
        self.update_current_target_temperature()

    def calculate_cpu_divisor_for_target_temp(self):
        """
        Calculate the divisor needed to reach the target temperature according to this formula (last line) :
        t = sense.get_temperature()
        p = sense.get_temperature_from_pressure()
        h = sense.get_temperature_from_humidity()
        c = get_cpu_temp()
        target_temperature = ((t+p+h)/3) - (c/divisor)
        :return: A float that has the value for what the divisor would be.
        """
        average_sense_hat_temp = (self.sense_hat_temp + self.sense_hat_temp_from_humidity +
                                  self.sense_hat_temp_from_pressure) / 3
        return self.cpu_temp / -(self.current_target_temperature - average_sense_hat_temp)

    def update_current_target_temperature(self):
        """
        This update the target temperature so that when we calculate the CPU divisor, it does not change when we log it.
        This is only in the case where the object TargetTemperature would be configured to gather temperature from an
        external sensor.
        """
        self.current_target_temperature = self.target_temperature.get_temperature()

    def update_cpu_temp(self):
        """
        This update the CPU temperature from "/opt/vc/bin/vcgencmd measure_temp".
        """
        os_command = os.popen('/opt/vc/bin/vcgencmd measure_temp')
        command_result = os_command.read()

        match = re.search('^temp=([^\']+)\'C$', command_result)
        self.cpu_temp = float(match.group(1))

    def get_cpu_temp(self):
        """
        This get the CPU temperature from "/opt/vc/bin/vcgencmd measure_temp".
        :return: A float containing the CPU temperature in Celsius.
        """
        os_command = os.popen('/opt/vc/bin/vcgencmd measure_temp')
        command_result = os_command.read()

        match = re.search('^temp=([^\']+)\'C$', command_result)
        return float(match.group(1))

    def update_sense_hat_temp(self):
        """
        Wrapper method for get_temperature for SensorHat.
        """
        self.sense_hat_temp = self.sense_hat.get_temperature()

    def update_sense_hat_temp_from_pressure(self):
        """
        Wrapper method for get_temperature_from_pressure for SensorHat.
        """
        self.sense_hat_temp_from_pressure = self.sense_hat.get_temperature_from_pressure()

    def update_sense_hat_temp_from_humidity(self):
        """
        Wrapper method for get_temperature_from_humidity for SensorHat.
        """
        self.sense_hat_temp_from_humidity = self.sense_hat.get_temperature_from_humidity()

    def update_cpu_load_average(self):
        load_averages = os.getloadavg()
        self.cpu_load_avg_1_min = load_averages[0]
        self.cpu_load_avg_5_min = load_averages[1]
        self.cpu_load_avg_15_min = load_averages[2]

    def get_cpu_usage(self):
        """
        This calculate the current CPU usage. The CPU stat times need to be updated before so call update_cpu_usage()
        first.
        :return: a float that has the CPU usage in the same style as the load average shown by the command uptime on
        Linux (i.e. 0.52 for 52% utilization of one CPU core).
        """
        delta_cpu_stats = self.get_delta_cpu_times()
        cpu_usage_in_percent = 100 - (delta_cpu_stats[len(delta_cpu_stats) - 1] * 100.0 / sum(delta_cpu_stats))
        # Calculate the CPU usage in the same format as the load average
        cpu_usage_in_cpu_core = cpu_usage_in_percent / 100 * 4

        return cpu_usage_in_cpu_core

    def update_cpu_usage(self):
        """
        Update the CPU stat times needed to calculate the current CPU usage. Note that this include a sleep.
        """
        self.update_cpu_stat_times()
        time.sleep(self.polling_interval)
        self.update_cpu_stat_times()

    def get_delta_cpu_times(self):
        """
        This calculate the difference between the current cpu times and the previous cpu times that were last updated
        roughly since the time_interval in seconds. The cpu times are gathered with update_cpu_times().
        :return: A list that contains the difference between the current cpu times and the previous cpu times.
        """
        delta_cpu_times = [None, None, None, None]
        for i in range(len(self.previous_cpu_times)):
            delta_cpu_times[i] = self.current_cpu_times[i] - self.previous_cpu_times[i]

        return delta_cpu_times

    def update_cpu_stat_times(self):
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

    def get_accelerometer_data(self):
        """
        Wrapper method for get_accelerometer_raw().
        :return: It returns a dictionary containing the acceleration on the x, y and z axis.
        """
        return self.sense_hat.get_accelerometer_raw()
