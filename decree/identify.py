import datetime
import logging
import os
import re
import xmltodict
import unicodedata

import pyudev
import requests
import requests_cache

from .utils import is_dvd, is_blu_ray

requests_cache.install_cache(backend='memory')
logger = logging.getLogger(__name__)


def search_tmdb(movie):
    logger.info("Searching TMDB for the movie release year")

    session = requests.session()
    session.params.update({
        'api_key': os.environ['TMDB_API_KEY'],
        'query': movie
    })
    session.headers.update({
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })

    resp = session.get('https://api.themoviedb.org/3/search/movie')
    if resp.status_code != 200:
        logger.error(f"TMDB query failed with response\n"
                     f"{resp.status_code}: {resp.reason}")
    return resp.json()


def get_tmdb_year(movie):
    results = search_tmdb(movie)
    if results['total_results'] == 0:
        logger.info("Did not find any results.")
        year = ""
    elif results['total_results'] > 1:
        logger.info("Found multiple results.")
        year = ""
    else:
        logger.info("Found exactly 1 result.")
        movie = results['results'][0]
        release_date = movie['release_date']
        year = datetime.datetime.strptime(release_date, '%Y-%m-%d').year

    return year


def get_movie_year(movie):
    year = get_tmdb_year(movie)
    if not year:
        year = get_omdb_year(movie)
    return year


def clean_blu_ray_title(title):
    title = (unicodedata.normalize('NFKD', title)
             .encode('ascii', 'ignore')
             .decode())
    tm = chr(8482)
    title = re.sub(r" - (Blu\-rayTM|BLU\-RAYTM|BLU\-RAY|Blu\-ray)", "", title)
    title = re.sub(tm, "", title)
    return title


def clean_title_for_search(title):
    return re.sub("_", " ", title)


def get_blu_ray_title(path):
    fname = f'{path}/BDMV/META/DL/bdmt_eng.xml'
    if not os.path.exists(fname):
        logger.info("Metadata XML not in expected location.")
        return ''

    with open(fname, 'rb') as xml_file:
        doc = xmltodict.parse(xml_file.read())

    title = doc['disclib']['di:discinfo']['di:title']['di:name']
    # TODO: Test a unicode title
    title = clean_blu_ray_title(title)

    return title


def _fetch_omdb(params):
    session = requests.session()
    session.params.update({
        'apikey': os.environ['OMDB_API_KEY'],
        'plot': 'short',
        'r': 'json',
        **params
    })
    logger.info("Querying OMDB.")
    resp = session.get('https://www.omdbapi.com/')

    if resp.status_code != 200:
        logger.error(f"OMDB query failed with response\n"
                     "{resp.status_code}: {resp.reason}")
        resp.raise_for_status()

    return resp.json()


def search_omdb(title):
    return _fetch_omdb({
        's': title
    })


def get_omdb(title, year):
    return _fetch_omdb({
        't': title,
        'y': year
    })


def get_omdb_year(title):
    logger.info("Attempting to get year from OMDB.")
    result = get_omdb(title, '')
    if result['Response'] == 'True':
        logger.info("Found exact title.")
        return result['Year']

    logger.info("Searching OMDB.")
    result = search_omdb(title)
    if result['Response'] == 'True':
        if result['totalResults'] == '1':
            logger.info("Found exactly 1 result.")
            return result['Search'][0]['Year']
        else:
            logger.info("Found multiple results.")
            return ''
    else:
        logger.info("Found no search results.")


def get_media_type(title, year=''):
    results = get_omdb(title, year)
    response = results['Response']
    if response == 'False' and year:
        error = results['Error']
        logger.info(f'Title {title} and year {year} not found.\n'
                    f'Error: {error}\nRetrying without year')
        return get_media_type(title, '')
    elif response == 'False':
        logger.info(f"Title {title} not found.")
    elif response == 'True':
        return results['Type']
    else:
        logger.error(f"Unhandled response\n{results}")


def get_title(path):
    if is_dvd(path):
        logger.info("Found DVD")
        logger.info("No reliable way to find DVD title")
        logger.info("Consider using libdvdnav")
        title = ''
    elif is_blu_ray(path):
        logger.info("Found Blu-Ray")
        title = get_blu_ray_title(path)
        if not title:
            logger.info("Failed to get Blu-Ray title from disc")
    else:
        msg = "Did not find a video on the device"
        logger.error(msg)
        raise ValueError(msg)

    return title


def identify(device_name, mount_point):
    assert 'TMDB_API_KEY' in os.environ
    assert 'OMDB_API_KEY' in os.environ

    logger.info("Identifying disk")
    context = pyudev.Context()

    # this is probably /dev/sr0 or something. Don't need the 'dev'
    device = pyudev.Devices.from_name(
        context,
        'block',
        device_name.split('/')[-1]
    )
    id_fs_type = device.get('ID_FS_TYPE')

    if id_fs_type != 'udf':
        # if it's 'iso9660, then a data rip might work.
        raise ValueError(f"Expected 'udf' for FS type. Got {id_fs_type}")

    title = get_title(mount_point)
    if not title:
        logger.info("Getting title from ID_FS_LABEL")
        title = device.get('ID_FS_LABEL')
        logger.info(f"ID_FS_LABEL: {title}")

    title = clean_title_for_search(title)
    year = get_movie_year(title)

    logger.info(f"Title: '{title}'; Year: {year}")

    # TODO: it's possible that this could find a new year for the title
    video_type = get_media_type(title, year)

    logger.info("Done with identification.")
    logger.info(f"Title: '{title}'; Year: {year}; Video Type: {video_type}")
    return title, year, video_type
