import click 
import sounddevice as sd

from .recorder import start_recording
from .settings import settings
    

# Click group settings

@click.group()
def cli(): pass


# Click individual commands

@cli.command()
def list():
    """
    Display all available audio devices.
    """
    click.echo(sd.query_devices())


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
def rec():
    """
    Start recording, indexing and uploading until interrupted.
    """
    if not settings.recorder:
        _set_recorder_settings()
    click.echo("Recording started. Press Ctrl+C to stop.")
    start_recording()


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


# Start Click
cli()
