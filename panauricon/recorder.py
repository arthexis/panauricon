import logging
import uuid
from pathlib import Path
from datetime import datetime
from queue import Queue
from threading import Event

import sounddevice as sd
import soundfile as sf
import sqlite_utils as su
import numpy as np
 
from .settings import settings


logger  = logging.getLogger('panauricon.recorder')


def start_recording():
    """
    Begin recording audio using existing settings.
    """
    device = _get_recording_device()
    soundfile_kwargs = _get_soundfile_kwargs(device)
    samplerate = soundfile_kwargs['samplerate']
    queue = Queue()
    context = {'silence': 0}

    def callback(indata, frame_count, time_info, status):
        if status:
            logger.info(f"Status in callback: {status}")
        # Mover el procesamiento aqui en lugar del loop abajo
        data = _process_block(indata.copy(), context)
        if data is not None:
            queue.put(data)

    with sd.InputStream(**settings.recorder, channels=1, callback=callback):
        now = datetime.utcnow()
        path = _get_recording_path(now)
        while True:
            id, filename = _get_uuid_filename(now)
            _insert_db_recording(id, path, filename, now, samplerate)
            try: 
                with sf.SoundFile(path / filename, mode='w', **soundfile_kwargs) as f:
                    while True:
                        now = datetime.utcnow()
                        if queue:
                            f.write(queue.get())
                        if (nextpath := _get_recording_path(now)) != path:
                            logger.info("Expired pathlist restart.")
                            path = nextpath
                            break
            finally:
                logger.info(f"Closed soundfile.")


def start_playback(start):
    """
    Begin recording audio using existing settings.
    """
    buffersize = int(settings.playback.buffersize or 20)
    blocksize = int(settings.playback.blocksize or 2048)
    device = _get_playback_device()
    hostapi = sd.query_hostapis(device['hostapi'])
    count = 0
    try:
        logger.info(f"Looking up playback fragments.")
        for r in _select_db_recordings_after(start):
            logger.info(f'Begin playback for {r["id"]}.')
            count += 1
            path = Path(r['path']) / r['filename']
            logger.info(f"Playback file: {str(path)}")
            _playback_fragment(path, device, hostapi, buffersize, blocksize)
    finally:
        logger.info(f"Played {count} recordings.")


def _playback_fragment(path, device, hostapi, buffersize, blocksize):
    queue = Queue(maxsize=buffersize)
    event = Event()
    device_name = f"{device['name']} {hostapi['name']}"

    def callback(outdata, frames, time, status):
        assert frames == blocksize
        if status.output_underflow:
            logger.warning('Output underflow: increase blocksize?')
            raise sd.CallbackAbort
        assert not status
        try:
            data = queue.get_nowait()
        except queue.Empty as e:
            logger.warning('Buffer is empty: increase buffersize?')
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
        else:
            outdata[:] = data

    with sf.SoundFile(path, mode='r') as f:
        for _ in range(buffersize):
            data = f.read(blocksize, always_2d=True)
            if not len(data):
                break
            queue.put_nowait(data)  # Pre-fill queue
        stream = sd.OutputStream(
            samplerate=f.samplerate, blocksize=blocksize, 
            channels=f.channels, device=device_name, 
            callback=callback, finished_callback=event.set)
        with stream:
            timeout = blocksize * buffersize / f.samplerate
            while len(data):
                data = f.read(blocksize, always_2d=True)    
                queue.put(data, timeout=timeout)

    
def _process_block(data, context):
    """
    Return the processed audio block or None.
    Raises StopIteration when the recording must restart.
    Context is used to hold state between blocks.
    """
    return data
    

def _get_recording_path(now: datetime):
    """
    Calculate the path and filename for the next sound file.
    """
    base_path = Path(settings.base_path or '.')
    path = base_path / settings.soundfile.root
    if not path.exists():
        path.mkdir()
        logger.info("Recordings path missing, created.")
    for part in settings.soundfile.pathlist:
        path = path / now.strftime(part)
        if not path.exists():
            path.mkdir()
            logger.info(f"New recording subfolder: {str(path)}")
    return path


def _get_uuid_filename(now: datetime):
    """
    Calculate the filename for the sound file.
    """
    prefix = now.strftime(settings.soundfile.prefix)
    id = uuid.uuid4()
    extension = settings.soundfile.format
    filename = f"{prefix}_{id}.{extension}"
    return id, filename


def __get_device(kind):
    _, portaudio_version = sd.get_portaudio_version()
    logger.debug(f"{portaudio_version}")
    device = sd.query_devices(device=settings.recorder.device, kind=kind)
    return device


def _get_recording_device():
    """
    Determine which device to use for the recording.
    """
    device = __get_device('input')
    logger.info(f"Using device='{device['name']}' for recording.")
    return device


def _get_playback_device():
    """
    Determine which device to use for the recording.
    """
    device = __get_device('output')
    logger.info(f"Using device='{device['name']}' for playback.")
    return device


def _get_soundfile_kwargs(device):
    """
    Return the soundfile options required by device.
    """
    assert device
    samplerate = int(device['default_samplerate'])
    return {
        'channels': 1, 
        'samplerate': samplerate
    }


# Database configuration

def _sql_tracer(sql, params):
    logger.debug("SQL: {} - params: {}".format(sql, params))


database = su.Database(settings.database, tracer=_sql_tracer)


def _insert_db_recording(id, path, filename, now, samplerate):
    database["recording"].insert({
        "id": id,
        "path": str(path),
        "filename": filename, 
        "start": now.strftime(r'%Y%m%d%H%M%S'),
        "format": settings.soundfile.format,
        "samplerate": samplerate,
        "app_version": settings.version,
    }, pk='id')


def _select_db_recordings_after(start):
    start = start.strftime(r'%Y%m%d%H%M%S')
    yield from database.query(
        "select * from recording where start >= :start",
        {'start': start}
    )

