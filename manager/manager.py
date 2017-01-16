from sense_hat import SenseHat


class Manager:
    """
    This is to manage the interactions between the joystick, screen and the data gatherer.
    """

    def __init__(self):
        self.sense_hat = SenseHat()

    def main_loop(self):
        while True:
            print("TDB")
            # TODO : continue with what's needed
