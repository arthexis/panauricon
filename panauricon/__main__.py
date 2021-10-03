import shutil
from pathlib import Path

import click 
import sounddevice as sd

from .settings import settings
    

# Click group settings

@click.group()
def cli(): pass


# Click individual commands

@cli.command()
@click.option('--full', is_flag=True)
def devices(full):
    """
    Display all available audio devices.
    """
    devices = sd.query_devices()
    if not full:
        click.echo(devices)
    else:
        for i, d in enumerate(devices):
            click.echo(f'Device #{i}')
            click.echo(d)


@cli.command()
@click.option('--get')
def config(get):
    """
    Configure the recording device and save the settings.
    """
    if get:
        click.echo(getattr(settings, get))
        return
    _set_recorder_settings()
    settings.dump()


@cli.command()
@click.option('-i', '--interactive', is_flag=True)
def rec(interactive):
    """
    Start recording, indexing and uploading until interrupted.
    """
    from .recorder import start_recording

    if interactive and not settings.recorder:
        _set_recorder_settings()
    click.echo("Recording started. Press Ctrl+C to stop.")
    start_recording()


@cli.command()
@click.option('--start', default='1 min ago')
def play(start):
    """
    Start playback from a specified time forwards.
    By default plays back the last minute.
    """
    import moment
    from .recorder import start_playback

    start = moment.utc(start)
    click.echo(f"Starting playback from {start}.")
    start_playback(start)


@cli.command()
def clean():
    """
    Delete all local operational data.
    """
    from pathlib import Path
    (settings.base_path / settings.database).unlink()
    shutil.rmtree(settings.base_path / settings.soundfile.root)
    click.echo("All local data removed.")


# Helper functions

def _set_recorder_settings():
    """
    Interactively choose an element from a list.
    """
    click.echo("Choose your recording device.")
    click.echo(sd.query_devices())
    device_id = input("Enter the number for your choice: ")
    settings.recorder = {
        'device': int(device_id) if device_id != "" else None
    }


try:
    cli()
except SystemExit:
    pass  # Not an error
