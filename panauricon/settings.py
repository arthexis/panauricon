import logging

import toml
import poetry_version


__version__ = str(poetry_version.extract(source_file=__file__))


SETTINGS_FILE = "settings.toml"
DEFAULT_SETTINGS = {
    'version': __version__,
    'format': 'flac', 
    'loglevel': 'INFO',
    'recorder': {}
}


class Settings(dict):
    """
    A structure that holds the current settings.
    You can use attribute access to access these settings.
    """

    def store(self):
        """
        Update the configuration file with current values.
        """
        with open(SETTINGS_FILE, "w") as f:
            toml.dump( {**DEFAULT_SETTINGS, **self}, f)

    def __getattr__(self, name):
        """
        Access the settings through attributes.
        """
        attr = super().get(name, None)
        if isinstance(attr, dict):
            return Settings(attr)

    def __setattr__(self, name: str, value):
        """
        Update a setting using attribute access.
        """
        super().setdefault(name, value)


# Global variable with the current settings
settings = Settings({**DEFAULT_SETTINGS, **toml.load(SETTINGS_FILE)})

# Setup logging from settings
logging.basicConfig(
    filename='recorder.log', 
    level=settings.loglevel,
    encoding='utf-8',
    format='%(asctime)s %(levelname)s: %(message)s'
)

logger  = logging.getLogger('panauricon.settings')
logger.info(f"Loaded settings file {SETTINGS_FILE}.")
logger.debug(f'Settings: {settings}')

