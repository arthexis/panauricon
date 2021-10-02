from pathlib import Path

import click 
import sounddevice as sd

from .recorder import record_loop
from .settings import settings


def pick_device():
    """Interactively choose an element from a list."""
    click.echo("Choose your recording device.")
    click.echo(sd.query_devices())
    choice = input("Enter the number for your choice: ")
    return int(choice) if choice != "" else None


@click.group()
def cli():
    pass


@cli.command()
def list():
    """Display available recording devices."""
    click.echo(sd.query_devices())


@cli.command()
def config():
    """"Configure the recorder."""
    settings['recorder'] = {'device': pick_device()}
    settings.store()


@cli.command()
def record():
    """Start recording until interrupted."""
    click.echo("Recording started. Press Ctrl+C to stop.")
    record_loop()


cli()
