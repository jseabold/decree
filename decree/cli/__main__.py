import logging

import click

from decree import blu_ray_rip, transcode, identify, dvd_rip
from decree.utils import is_dvd, is_blu_ray, parse_config, mount, unmount

logger = logging.getLogger(__name__)


# this is smelly. could export these to the env and use autoenv but that also
# seems wrong.
try:
    DEVICE_NAME, MOUNT_POINT, RAW_PATH, FINAL_PATH = parse_config()
except FileNotFoundError:
    pass


@click.group()
def cli():
    pass


@click.command()
@click.option('--device-name', default=DEVICE_NAME, type=click.Path(),
              help="Device name. E.g., /dev/sr0")
@click.option('--mount-point', type=click.Path(), default=MOUNT_POINT,
              help="Where the device will be mounted.")
def cli_identify(device_name, mount_point):
    if not mount_point or not device_name:
        raise ValueError("Must supply values for both --device-name and"
                         " --mount-point if not specified in config.yaml")
    mount(device_name, mount_point, automount=True)
    try:
        title, year, video_type = identify(device_name, mount_point)
    finally:
        unmount(MOUNT_POINT)


@click.command()
@click.option('--output-dir', default=RAW_PATH, type=click.Path(),
              help='Directory for the final, raw mkv file.')
@click.option('--device-name', default=DEVICE_NAME, type=click.Path(),
              help="Device name. E.g., /dev/sr0")
@click.option('--title', required=True, help="The movie title")
@click.option('--year', required=True, help="The release year")
def cli_blu_ray_rip(output_dir, device_name, title, year):
    destination, now = blu_ray_rip(output_dir, device_name, title, year, None)


@click.command()
@click.option('--output-dir', default=FINAL_PATH, type=click.Path(),
              help='Directory for the final, raw mkv file.')
@click.option('--input-dir', default=MOUNT_POINT, type=click.Path(),
              help="The directory where the DVD is mounted.")
@click.option('--title', required=True, help="The movie title")
@click.option('--year', required=True, help="The release year")
def cli_dvd_rip(output_dir, input_dir, title, year):
    dvd_rip(output_dir, input_dir, title, year)


@click.command()
@click.option('--output-dir', default=FINAL_PATH,
              type=click.Path(exists=True),
              help='Directory for final mkv file.')
@click.option('--input-dir', type=click.Path(exists=True),
              help='Directory with single, raw mkv file.')
@click.option('--title', required=True, help="Movie title.")
@click.option('--year', required=True, help="Movie year.")
@click.option('--input-file', type=click.Path(exists=True),
              help="Raw mkv file to process, optional. Useful for more than"
              "one mkv file in the input directory.")
def cli_transcode(output_dir, input_dir, title, year, input_file):
    if input_dir and input_file:
        raise ValueError("Specify only one --input-dir or --input-file")
    if output_dir is None:
        raise ValueError("--output-dir must be specified in config.yaml or "
                         "provided")
    transcode(output_dir, input_dir, title, year, input_file=input_file)


@click.command()
@click.option('--device-name', default=DEVICE_NAME, type=click.Path(),
              help="Device name. E.g., /dev/sr0")
@click.option('--mount-point', type=click.Path(), default=MOUNT_POINT,
              help="Where the device will be mounted.")
@click.option('--raw-output-dir', default=RAW_PATH, type=click.Path(),
              help='Directory for the final, raw mkv file.')
@click.option('--final-output-dir', default=FINAL_PATH, type=click.Path(),
              help='Directory for the final encoded mkv file.')
@click.option('--title', help='Required for DVD input.')
@click.option('--year', help='Required for DVD input')
def end_to_end(device_name, mount_point, raw_output_dir, final_output_dir,
               title, year):
    if not mount_point or not device_name:
        raise ValueError("Must supply values for both --device-name and"
                         " --mount-point if not specified in config.yaml")
    mount(device_name, mount_point, automount=True)

    if is_blu_ray(mount_point):
        try:
            title, year, video_type = identify(device_name, mount_point)
        finally:
            unmount(mount_point)
        destination, now = blu_ray_rip(raw_output_dir, device_name, title,
                                       year, None)
        transcode(final_output_dir, destination, title, year, now)

    elif is_dvd(mount_point):
        if not title or not year:
            logger.error("--title and --year are required for a DVD input.")
        try:
            dvd_rip(final_output_dir, mount_point, title, year)
        finally:
            unmount(mount_point)
    else:
        unmount(mount_point)
        logger.error("Media type not recognized")


cli.add_command(cli_blu_ray_rip, 'blu-ray-rip')
cli.add_command(cli_identify, 'identify')
cli.add_command(cli_transcode, 'transcode')
cli.add_command(end_to_end)
cli.add_command(cli_dvd_rip, 'dvd-rip')

if __name__ == "__main__":
    cli()
