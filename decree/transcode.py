import glob
import logging
import os
import re

from pymediainfo import MediaInfo

from .utils import get_now, run_and_log_subprocess

logger = logging.getLogger(__name__)


def get_video_general_tracks(tracks):
    video_tracks = list(filter(
        lambda x: x.track_type == 'Video',
        tracks
    ))
    # the general track has a `count_of_X_streams parameter
    if len(video_tracks) > 1:
        msg = "More than one video track found."
        logger.error(msg)
        raise ValueError(msg)
    video_track = video_tracks[0]

    general_tracks = list(filter(
        lambda x: x.track_type == 'General',
        tracks
    ))
    if len(general_tracks) > 1:
        msg = "More than one general track found."
        logger.error(msg)
        raise ValueError(msg)
    general_track = general_tracks[0]
    return video_track, general_track


def get_bitrate(video_track, general_track):
    width = video_track.width
    height = video_track.height
    if (width > 1280) or (height > 720):
        max_bitrate = 6500
    elif (width > 720) and (height > 576):
        max_bitrate = 4000
    else:
        max_bitrate = 1800

    min_bitrate = max_bitrate // 2
    bitrate = video_track.bit_rate

    if not bitrate:
        bitrate = general_track.overall_bit_rate
        bitrate = (bitrate // 10) * 9

    if bitrate:  # how could this not be satisfied?
        bitrate = (bitrate // 5) * 4
        bitrate = bitrate // 1000
        bitrate = (bitrate // 100) * 100
        bitrate = max(bitrate, max_bitrate)
        bitrate = min(bitrate, min_bitrate)
    else:
        bitrate = min_bitrate
    return ['--vb', f'{bitrate}']


def get_frame_rate(video_track):
    frame_rate = video_track.frame_rate_original
    if not frame_rate:
        frame_rate = video_track.frame_rate

    # TODO: I'm not sure why we make the frame rate lower
    if frame_rate == '29.970':
        frame_rate = ['--rate', '23.976']
    else:
        frame_rate = ['--rate', '30', '--pfr']
    return frame_rate


def get_media_info(mkv):
    media_info = MediaInfo.parse(mkv)
    video_track, general_track = get_video_general_tracks(media_info.tracks)
    bitrate = get_bitrate(video_track, general_track)
    frame_rate = get_frame_rate(video_track)
    channels = get_audio_channels(media_info.tracks, general_track)
    return bitrate, frame_rate, channels


def get_audio_channels(tracks, general_track):
    audio_channels = f''.join(f'{_.channel_s}' for _ in tracks if _.channel_s)
    channel = int(re.sub('[^0-9].*$', '', audio_channels))
    if channel > 2:
        channel = ['--aencoder', 'ca_aac,copy:ac3']
    elif general_track.audio_format_list.split(' / ')[0] == 'AAC':
        channel = ['--aencoder', 'copy:aac']
    else:
        channel = []
    return channel


def transcode(final_path, input_folder, title, year, now=None,
              input_file=None):
    # this is based totally on https://gist.github.com/donmelton/5734177
    # there's a newer ruby library
    # https://github.com/donmelton/video_transcoding/
    # that's looks a little higher fire power
    destination = f'{final_path}/{title} ({year})'
    if os.path.exists(destination):
        logger.info(f"Destination {destination} exists. Adding timestamp.")
        if not now:
            now = get_now()
        destination += f"_{now}"
    os.makedirs(destination)

    output = f'{destination}/{title} ({year}).mp4'
    if not input_file:
        input_files = glob.glob(f'{input_folder}/*.mkv')
        if len(input_files) > 1:
            msg = (
                f'More than one mkv file found in {input_folder}. '
                'Specify the input file'
            )
            logger.error(msg)
            raise ValueError(msg)

        input_file = input_files[0]
    else:
        exists = os.path.exists(input_file)
        if not exists:
            msg = f'File {input_file} does not exist'
            logger.error(msg)
            raise FileNotFoundError(msg)

    handbrake_options = [
        '--markers',
        '--large-file',
        '--encoder', 'x264',
        '--encopts', 'vbv-maxrate=25000:vbv-bufsize=31250:ratetol=inf',
        '--crop', '0:0:0:0',
        '--strict-anamorphic'
    ]
    bitrate, frame_rate, audio_channels = get_media_info(input_file)

    handbrake_options += [
        *bitrate,
        *frame_rate,
        *audio_channels
    ]

    cmd = ['HandBrakeCLI'] + handbrake_options
    cmd += ['--input', input_file, '--output', output]
    # since this does a progress bar update to stdout, the approach
    # here doesn't log updates until a new chapter
    run_and_log_subprocess(cmd)
    logger.info('Finished transcoding.')
