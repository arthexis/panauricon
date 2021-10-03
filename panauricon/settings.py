import logging
from pathlib import Path

import toml
import poetry_version


__version__ = str(poetry_version.extract(source_file=__file__))


# Setup logging from settings

logging.basicConfig(
    filename='app.log', 
    level=logging.DEBUG,
    encoding='utf-8',
    format='%(asctime)s %(levelname)s: %(message)s'
)

logger  = logging.getLogger('panauricon.settings')


SETTINGS_FILE = Path("settings.toml")
DEFAULT_SETTINGS = {
    'version': __version__,
    'base_path': '.',
    'soundfile': {
        'format': 'flac', 
        'root': 'recordings', 
        'pathlist': [r'%Y', r'%m', r'%d', r'%H'],
        'prefix': r'%M%S',
    }, 
    'database': 'sqlite.db',
    'recorder': {},
    'playback': {
        'blocksize': 2048, 
        'buffersize': 20
    }
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
        return attr

    def __setattr__(self, name: str, value):
        """
        Update a setting using attribute access.
        """
        super().setdefault(name, value)

    @property
    def base_path(self):
        return Path(self.get('base_path'))


# Global variable with the current settings
settings = Settings(DEFAULT_SETTINGS)

if SETTINGS_FILE.exists():
    settings.load(SETTINGS_FILE)
else:
    logger.info('Using default settings.')

