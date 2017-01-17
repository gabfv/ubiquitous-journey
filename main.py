from manager.manager import Manager

# Config
log_time_interval = 0.5
log_filename = '/tmp/sensehat_log'
log_data_separator = ';'

if __name__ == '__main__':
    manager = Manager()
    manager.run_with_logging(log_time_interval, log_filename, log_data_separator)