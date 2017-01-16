class TargetTemperature:
    """
    This class would normally be for obtaining temperature from a reliable temperature sensor that is external to the
    RaspberryPi and the SensorHat. However, since I do not currently have one that allow me to easily obtain
    temperature, I will rely on an user configurable target temperature for now.
    """
    type = 'Celsius'

    def __init__(self, temperature):
        self.temperature = temperature

    def get_temperature(self):
        return self.temperature

    def set_temperature(self, temperature):
        """
        Set the temperature (in Celsius) only if it is between 0 and 70, according to the operating temperature of the
        RaspberryPi as specified at : https://www.raspberrypi.org/help/faqs/#performanceOperatingTemperature
        :param temperature:
        :return temperature:
        """
        if 0 <= temperature <= 70:
            self.temperature = temperature

        return self.temperature
