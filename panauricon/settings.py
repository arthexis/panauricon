import toml
import poetry_version


SETTINGS_FILE = "settings.toml"
DEFAULT_OPTS = {
    'version': str(poetry_version.extract(source_file=__file__)),
}


class Settings(dict):
    def store(self):
        """Update the configuration file."""
        with open(SETTINGS_FILE, "w") as f:
            toml.dump( {**DEFAULT_OPTS, **self}, f)


# Global variable with the current settings
settings = Settings({**DEFAULT_OPTS, **toml.load(SETTINGS_FILE)})
