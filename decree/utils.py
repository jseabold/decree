import datetime
import logging
import os
import subprocess
import yaml

logger = logging.getLogger(__name__)


def is_dvd(path):
    return os.path.exists(f'{path}/VIDEO_TS')


def is_blu_ray(path):
    return os.path.exists(f'{path}/BDMV')


def get_now():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def parse_config(config='config.yaml'):
    logger.info(f'Loading config file {config}')
    with open(config) as ymlfile:
        cfg = yaml.load(ymlfile)
    return (
        cfg['DEVICE_NAME'],
        cfg['MOUNT_POINT'],
        cfg['RAW_PATH'],
        cfg['FINAL_PATH']
    )


def run_and_log_subprocess(cmd):
    command = ' '.join(cmd)
    logger.info(f'Running command: \'{command}\'')
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    for line in iter(p.stdout.readline, b''):
        logger.info(line.decode('utf-8'))
    return p


def unmount(target):
    logger.info(f"Unmounting {target}")
    p = run_and_log_subprocess(['umount', target])

    if p.returncode and p.returncode != 0:
        raise OSError("Failed to unmount disk. See LOG.")


def mount(source, target, automount=True):
    if automount:
        logger.info(f"Attempting to automount {source}")
        cmd = ['mount', source]
    else:
        logger.info(f"Attempting to mount {source} at {target}")
        cmd = ['mount', source, target]

    p = run_and_log_subprocess(cmd)

    if p.returncode and p.returncode != 0:
        raise OSError("Failed to mount disk. See LOG. Perhaps you need "
                      "to edit /etc/fstab so your user can mount?")

    logger.info(f"Mounted {source}")
