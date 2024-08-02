import configparser

class Settings:
    def __init__(self, config_file='settings.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self._cache = {}

    def _get_cached(self, section, key, default=None, cast_func=str):
        if (section, key) not in self._cache:
            if cast_func == self.config.getboolean:
                # Special case for boolean values
                value = self.config.getboolean(section, key)
            else:
                # Default case for other types
                value = self.config.get(section, key, fallback=default)
                value = cast_func(value)
            self._cache[(section, key)] = value
        return self._cache[(section, key)]

    def get(self, section, key, default=None):
        """Get a string value from the configuration."""
        return self._get_cached(section, key, default)

    def get_int(self, section, key, default=0):
        """Get an integer value from the configuration."""
        return self._get_cached(section, key, default, int)

    def get_float(self, section, key, default=0.0):
        """Get a float value from the configuration."""
        return self._get_cached(section, key, default, float)

    def get_boolean(self, section, key, default=False):
        """Get a boolean value from the configuration."""
        return self._get_cached(section, key, default, str)

    def set(self, section, key, value):
        """Set a value in the configuration file, creating sections if necessary."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def save(self, config_file='settings.ini'):
        """Save the current configuration to a file."""
        with open(config_file, 'w') as f:
            self.config.write(f)
