import logging
from pathlib import Path
from datetime import datetime
from queue import Queue

import sounddevice as sd
import soundfile as sf

from .settings import settings


logging.basicConfig(
    filename='recorder.log', 
    level=logging.INFO,
    encoding='utf-8',
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger  = logging.getLogger(__name__)


def get_recording_path(root, now):
    path: Path = root / 'recordings'
    if not path.exists():
        path.mkdir()
    path = path / now.strftime(r'%Y%d%m')
    if not path.exists():
        path.mkdir() 
    return path / now.strftime(r'%H%M%S.wav')


def record_loop():
    opts = settings['recorder']
    device = sd.query_devices(device=opts.get('device'), kind='input')
    samplerate = float(device['default_samplerate'])
    root = Path(settings.pop('path', '.'))
    queue = Queue()

    def callback(indata, frame_count, time_info, status):
        if status:
            logger.info(f"{status}")
        queue.put(indata.copy())

    with sd.InputStream(**opts, channels=1, callback=callback):
        logger.info("Opening input stream.")
        while True:
            now = datetime.utcnow()
            path = get_recording_path(root, now)
            with sf.SoundFile(path, mode='w', channels=1, samplerate=int(samplerate)) as f:
                while now.minute == datetime.utcnow().minute:
                    f.write(queue.get())
