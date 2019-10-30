```
 (                     (
 )\ )            (     )\ )
 (()/(    (       )\   (()/(   (     (
 /(_))   )\    (((_)   /(_))  )\    )\
 (_))_   ((_)   )\___  (_))   ((_)  ((_)
  |   \  | __| ((/ __| | _ \  | __| | __|
  | |) | | _|   | (__  |   /  | _|  | _|
  |___/  |___|   \___| |_|_\  |___| |___|
```

This code attempts to automatically identify metadata and orchestrate other tools to rip and transcode DVDs and Blu-Rays into `mkv` files. Due to inconsistencies among different media, it relies on a happy path to work.

## Requirements

This is only known to work on Linux. You'll need working versions of [makemkvcon](https://www.makemkv.com/) and [HandBrakeCLI](https://handbrake.fr/downloads.php) on your path.

## Installation

```bash
git clone git@github.com:jseabold/decree.git
cd decree
pip install -r requirements.txt
pip install .
```

## Configuration

You can configure four variables via a `config.yaml` file. The DEVICE_NAME is your drive (e.g., /dev/sr0). The MOUNT_POINT is where you would like to mount the drive. If you have configured the drive to automount, then this is optional. RAW_PATH is the directory in which the raw, uncompressed mkv files are placed after the rip step. FINAL_PATH is where the final, compressed mkv files are placed after transcoding.

## API Keys

This requires two API keys for querying metadata. [The Movie DB](https://www.themoviedb.org/) and [The Open Movie Database](https://www.omdbapi.com/). The keys are expected to be in the environment variables `TMDB_API_KEY` and `OMDB_API_KEY`, respectively.

## Usage

This can be used as a Python package or via the provided command-line interface. See `decree --help` for CLI usage instructions. If you want tab-completion for the CLI, source the appropriate .sh file for either bash or zsh.

## Prior Art

The identification and ripping steps are inspired by the bash scripts in the [Automatic Ripping Machine](https://github.com/automatic-ripping-machine/automatic-ripping-machine) project. The transcoding step and its settings are inspired by [this script](https://gist.github.com/donmelton/5734177).

## Credits

This product uses the TMDb API but is not endorsed or certified by TMDb.
