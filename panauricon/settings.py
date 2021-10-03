import logging
from pathlib import Path

import toml
import poetry_version


__version__ = str(poetry_version.extract(source_file=__file__))


SETTINGS_FILE = Path("settings.toml")
DEFAULT_SETTINGS = {
    'version': __version__,
    'soundfile': {'format': 'flac'}, 
    'loglevel': logging.DEBUG,
    'recorder': {}
}


class Settings(dict):
    """
    A structure that holds the current settings.
    You can use attribute access to access these settings.
    """

    def load(self):
        """
        Load settings from the configuration file.
        """
        loaded = toml.load(SETTINGS_FILE)
        for k, v in loaded.items():
            self[k] = v

    def dump(self, filename):
        """
        Update the configuration file with current values.
        """
        with open(filename, "w") as f:
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
settings = Settings({**DEFAULT_SETTINGS})

if SETTINGS_FILE.exists():
    settings.load(SETTINGS_FILE)
    

# Setup logging from settings

logging.basicConfig(
    filename='recorder.log', 
    level=settings.loglevel,
    encoding='utf-8',
    format='%(asctime)s %(levelname)s: %(message)s'
)

logger  = logging.getLogger('panauricon.settings')
logger.debug(f'Settings: {str(settings)}')

