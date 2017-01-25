import sys

from manager.manager import Manager

# Config
if sys.argv[1]:
    log_filename = sys.argv[1]
else:
    log_filename = '/tmp/sensehat_log'

log_polling_interval = 0.5
log_data_separator = ';'

if __name__ == '__main__':
    manager = Manager()
    manager.run_with_data_gatherer(log_polling_interval, log_filename, log_data_separator)
