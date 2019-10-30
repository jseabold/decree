import datetime
import logging
import os
import re

from .utils import run_and_log_subprocess

logger = logging.getLogger(__name__)


def clean_for_filename(name):
    """ Cleans up string for use in filename """
    name = re.sub(r'\[(.*?)\]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.replace(' : ', ' - ')
    name = name.replace(': ', ' - ')
    return re.sub(r'[^\w\-_\.\(\) ]', '', name)


def get_good_title(title, year):
    good_title = clean_for_filename(title)
    if not year:
        year = 'unknown'
    good_title = f'{good_title} ({year})'
    return good_title


def make_destination(path, title, year):
    good_title = get_good_title(title, year)

    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    destination = f'{path}/{good_title}_{now}'
    logger.info(f"Making destination folder {destination}")
    os.makedirs(destination)

    return destination, now


def dvd_rip(final_path, mount_path, title, year):
    good_title = get_good_title(title, year)
    if os.path.exists(f'{mount_path}/video_ts'):
        path = f'{mount_path}/video_ts'
    if os.path.exists(f'{mount_path}/VIDEO_TS'):
        path = f'{mount_path}/VIDEO_TS'
    else:
        path = mount_path

    os.makedirs(f'{final_path}/{good_title}/')

    cmd = [
        'HandBrakeCLI',
        '-i', path,
        '-o', f'{final_path}/{good_title}/{good_title}.mkv',
        '--crop', '0:0:0:0',
        '--preset="High Profile"'
    ]

    run_and_log_subprocess(cmd)
    logger.info('Finished ripping.')


def blu_ray_rip(RAW_PATH, DEVNAME, title, year, video_type, minlength=4000):
    logger.info("Starting ripping.")
    destination, now = make_destination(RAW_PATH, title, year)
    cmd = [
        'makemkvcon',
        'mkv',
        f'dev:{DEVNAME}',
        'all',
        destination,
        f'--minlength={minlength}',
        '-r'
    ]

    run_and_log_subprocess(cmd)
    logger.info("Finished ripping.")
    return destination, now
