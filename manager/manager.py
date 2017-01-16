from sense_hat import SenseHat


class Manager:
    """
    This is to manage the interactions between the joystick, screen and the data gatherer.
    """

    def __init__(self):
        self.sense_hat = SenseHat()

    def main_loop(self):
        while True:
            self.update_screen_rotation()
            # TODO : continue with what's needed

    def update_screen_rotation(self):
        acceleration_x = self.sense_hat.get_accelerometer_raw().['x']
        acceleration_y = self.sense_hat.get_accelerometer_raw().['y']

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