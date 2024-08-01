import configparser

class Settings:
    def __init__(self, config_file='settings.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get(self, section, key, default=None):
        """Get a string value from the configuration."""
        return self.config.get(section, key, fallback=default)

    def get_int(self, section, key, default=0):
        """Get an integer value from the configuration."""
        return self.config.getint(section, key, fallback=default)

    def get_float(self, section, key, default=0.0):
        """Get a float value from the configuration."""
        return self.config.getfloat(section, key, fallback=default)

    def get_boolean(self, section, key, default=False):
        """Get a boolean value from the configuration."""
        return self.config.getboolean(section, key, fallback=default)

    def set(self, section, key, value):
        """Set a value in the configuration file, creating sections if necessary."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def get_float_list(self, section, key, default=None):
        """Get a list of floats from the configuration."""
        string_value = self.get(section, key, default='[]')
        values_as_strings = string_value.strip('[]').split(',')
        return [float(value) for value in values_as_strings]

    def save(self, config_file='settings.ini'):
        """Save the current configuration to a file."""
        with open(config_file, 'w') as f:
            self.config.write(f)
