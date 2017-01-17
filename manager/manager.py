import threading
import time
from queue import Queue

from sense_hat import SenseHat

from data_gatherer.gatherer import Gatherer
from target_temp.target_temp import TargetTemperature


class Manager:
    """
    This is to manage the interactions between the joystick, screen and the data gatherer. It will allow screens showing
    different information to be switched with the left/right joystick directions, values to be changed with up/down
    directions and toggle the screen with the push action.
    """

    screen_order = ['Temperature', 'Pressure', 'Humidity', 'Set Target Temperature', 'Logging Start/Off']
    green = (0, 255, 0)
    red = (255, 0, 0)
    blue = (0, 0, 255)
    white = (255, 255, 255)
    nb_pixels_on_screen = 64

    def __init__(self):
        self.sense_hat = SenseHat()
        self.screen_index = 0
        self.value_index = 0
        self.target_temperature = TargetTemperature()
        self.screen_title_shown = False
        self.gatherer_thread = None
        self.gatherer_thread_logging_active = False
        self.queue_start_logging = Queue(maxsize=1)

    def run(self):
        self.main_loop()

    def run_with_logging(self, log_time_interval, log_filename, log_data_separator):
        self.start_data_gatherer_thread(log_time_interval, log_filename, log_data_separator)
        self.run()

    def main_loop(self):
        while True:
            self.update_screen_rotation()
            self.manage_joystick_events()
            self.update_screen()

    def start_data_gatherer_thread(self, log_time_interval, log_filename, log_data_separator):
        self.gatherer_thread = threading.Thread(target=Gatherer, args=(self.queue_start_logging, log_time_interval,
                                                                       log_filename, log_data_separator,
                                                                       self.target_temperature))
        self.gatherer_thread.daemon = True
        self.gatherer_thread.start()

    def update_screen_rotation(self):
        """
        Update the rotation of the SensorHat screen according to its accelerometer data.
        """
        acceleration_x = self.sense_hat.get_accelerometer_raw()['x']
        acceleration_y = self.sense_hat.get_accelerometer_raw()['y']

        acceleration_x = round(acceleration_x, 0)
        acceleration_y = round(acceleration_y, 0)

        if acceleration_x == -1:
            self.sense_hat.set_rotation(90)
        elif acceleration_y == 1:
            self.sense_hat.set_rotation(0)
        elif acceleration_y == -1:
            self.sense_hat.set_rotation(180)
        else:
            self.sense_hat.set_rotation(270)
        # TODO: include a way to rotate the joystick as well?

    def manage_joystick_events(self):
        """
        Process the events generated by the SenseHat joystick.
        """
        joystick_events = self.sense_hat.stick.get_events()

        for joystick_event in joystick_events:
            # The joystick push is a special event. It'll turn off the screen.
            if joystick_event.direction is 'middle':
                self.turn_off_screen_and_wait_for_user_action()
            elif joystick_event.action is not 'released':
                self.update_screen_index(joystick_event)

    def turn_off_screen_and_wait_for_user_action(self):
        """
        Turn off the screen and wait until the joystick is pushed. Do not react to other joystick events.
        """
        self.sense_hat.clear()

        # We should pause execution until the joystick is pushed.
        screen_off = True
        while screen_off:
            joystick_event = self.sense_hat.stick.wait_for_event(emptybuffer=True)
            if joystick_event.direction is 'middle':
                self.update_screen()
                screen_off = False

    def update_screen_index(self, joystick_event):
        """
        Update the screen index from the joystick event.
        :param joystick_event: The joystick event from which we will update
        """
        if joystick_event.direction is 'left':
            self.screen_index -= 1
            self.value_index = 0  # We don't want the values to carry through other screens.
            self.screen_title_shown = False
        elif joystick_event.direction is 'right':
            self.screen_index += 1
            self.value_index = 0  # We don't want the values to carry through other screens.
            self.screen_title_shown = False
        elif joystick_event.direction is 'down':
            self.value_index -= 1
        elif joystick_event.direction is 'up':
            self.value_index += 1

    def update_screen(self):
        """
        Update the current screen shown on the SenseHat.
        """
        self.show_screen_title()

        current_screen_index = self.screen_index % len(Manager.screen_order)
        if Manager.screen_order[current_screen_index] == 'Temperature':
            self.update_screen_for_temperature()
        elif Manager.screen_order[current_screen_index] == 'Humidity':
            self.update_screen_for_humidity()
        elif Manager.screen_order[current_screen_index] == 'Pressure':
            self.update_screen_for_pressure()
        elif Manager.screen_order[current_screen_index] == 'Set Target Temperature':
            self.update_screen_for_set_target_temperature()
        elif Manager.screen_order[current_screen_index] == 'Logging Start/Off':
            self.update_screen_for_manage_logging()

    def show_screen_title(self):
        """
        Show a screen title only once per screen change.
        """
        if not self.screen_title_shown:
            colors = [Manager.red, Manager.blue, Manager.green]
            current_color_index = self.screen_index % len(colors)
            current_screen_index = self.screen_index % len(Manager.screen_order)

            self.sense_hat.show_letter(Manager.screen_order[current_screen_index][0],
                                       back_colour=colors[current_color_index])
            time.sleep(.5)
            self.screen_title_shown = True

    def update_screen_for_manage_logging(self):
        """
        Update the screen for managing the logging about the SenseHat and RaspberryPi various sensors.
        """
        if self.value_index > 0:
            self.queue_start_logging.put(True)
            self.gatherer_thread_logging_active = True
        elif self.value_index < 0:
            self.queue_start_logging.put(False)
            self.gatherer_thread_logging_active = False

        if self.gatherer_thread.is_alive() and self.gatherer_thread_logging_active:
            self.sense_hat.show_letter('|', back_colour=Manager.green)
        elif not self.gatherer_thread_logging_active:
            self.sense_hat.show_letter('O', back_colour=Manager.red)

        self.value_index = 0

    def update_screen_for_set_target_temperature(self):
        """
        Update the screen for setting the target temperature.
        """
        current_target_temperature = self.target_temperature.get_temperature()
        self.sense_hat.show_message(str(current_target_temperature))

        # Update the target temperature if the user pressed the up/down joystick.
        if not self.value_index == 0:
            current_target_temperature += self.value_index * 0.5
            self.target_temperature.set_temperature(current_target_temperature)
            self.value_index = 0

    def update_screen_for_pressure(self):
        """
        Update the screen for the pressure screens.
        """
        pressure = self.sense_hat.get_pressure()
        current_value_index = self.value_index % 2

        if current_value_index == 0:
            self.sense_hat.show_message(str(round(pressure, 2)))
        elif current_value_index == 1:
            screen_fill_for_pressure = pressure / 20
            pixels = [Manager.green if i < screen_fill_for_pressure else Manager.white
                      for i in range(Manager.nb_pixels_on_screen)]
            self.sense_hat.set_pixels(pixels)

    def update_screen_for_humidity(self):
        """
        Update the screen for the humidity screens.
        """
        # TODO: Since the temperature sensor isn't that accurate, we'll need to update it in another way that is
        # calculated.
        humidity = self.sense_hat.get_humidity()
        current_value_index = self.value_index % 2

        if current_value_index == 0:
            # TODO: Temporary for a test. Should work it up to include a formula.
            self.sense_hat.show_message(str(round(humidity, 2)))
        elif current_value_index == 1:
            screen_fill_for_humidity = Manager.nb_pixels_on_screen * humidity / 100
            pixels = [Manager.blue if i < screen_fill_for_humidity else Manager.white
                      for i in range(Manager.nb_pixels_on_screen)]
            self.sense_hat.set_pixels(pixels)

    def update_screen_for_temperature(self):
        """
        Update the screen for the temperature screens.
        """
        temperature = self.sense_hat.get_temperature()
        current_value_index = self.value_index % 2

        if current_value_index == 0:
            # TODO: Temporary for a test. Should work it up to include a formula.
            self.sense_hat.show_message(str(round(temperature, 2)))
        elif current_value_index == 1:
            screen_fill_for_temp = temperature / 2.5 + 16
            pixels = [Manager.red if i < screen_fill_for_temp else Manager.white
                      for i in range(Manager.nb_pixels_on_screen)]
            self.sense_hat.set_pixels(pixels)

