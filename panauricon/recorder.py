import logging
from pathlib import Path
from datetime import datetime
from queue import Queue

import sounddevice as sd
import soundfile as sf

from .settings import settings


logger  = logging.getLogger('panauricon.recorder')


def start_recording():
    """
    Begin recording audio using existing settings.
    """
    device = _get_recording_device()
    soundfile_kwargs = _get_soundfile_kwargs(device)
    queue = Queue()
    context = {'silence': 0}

    def callback(indata, frame_count, time_info, status):
        if status:
            logger.info(f"Status in callback: {status}")
        queue.put(indata.copy())

    with sd.InputStream(**settings.recorder, channels=1, callback=callback):
        while True:
            path, filename = _get_recording_path()
            logger.info(f"Open {path=} {filename=} for writting.")
            try:
                with sf.SoundFile(path / filename, mode='w', **soundfile_kwargs) as f:
                    while data := _process_block(queue.get(), context):
                        f.write(data)
            finally:
                logger.info(f"Closed {path=} {filename=}.")


def _process_block(data, context):
    """
    Return the processed audio block or None.
    A return of None implies recording should be restarted.
    Context is used to hold state between blocks.
    """
    return data
    

def _get_recording_path():
    """
    Calculate the path and filename for the next sound file.
    """
    now = datetime.utcnow()
    root = Path(settings.path or '.')
    path = root / 'recordings'
    if not path.exists():
        path.mkdir()
        logger.info("Recordings path missing, created.")
    filename = now.strftime(r'%Y%m%d%H%M%S') + '.' + settings.format
    return path, filename


def _get_recording_device():
    """
    Determine which device to use for the recording.
    """
    _, portaudio_version = sd.get_portaudio_version()
    logger.info(f"{portaudio_version}")
    if not settings.recorder:
        return None
    device = sd.query_devices(device=settings.recorder.device, kind='input')
    logger.info(f"Using {device['name']=} for recording.")
    return device


def _get_soundfile_kwargs(device):
    """
    Return the soundfile options required by device.
    """
    return {
        'channels': 1, 
        'samplerate': int(device['default_samplerate'])
    }
