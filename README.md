# Plex Metadata Date Updater

A robust, user-friendly command-line tool to modify the "Date Added" metadata for items in your Plex Media Server. 

This script is useful if you have migrated your Plex library, replaced file versions, or manually added content and want to preserve or correct the order in which items appear in the "Recently Added" hub.

## Features

* **Robust Search:** Safely searches for items and confirms they exist before attempting edits.
* **Dry Run Mode:** Preview what changes will be made without actually altering your database.
* **Secure:** Supports Environment Variables for Plex Tokens to keep credentials out of your command history.
* **Flexible:** Works on Movies, TV Shows, or any other library section.
* **Date Parsing:** Accepts both `YYYY-MM-DD` and `YYYY-MM-DD HH:MM:SS` formats.

## Prerequisites

* Python 3.6+
* [PlexAPI](https://github.com/pkkid/python-plexapi)

### Installation

1.  Clone this repository or download the script.

2.  Create and activate a virtual environment (recommended to keep dependencies isolated):

    **Linux / macOS:**
    ```bash
    python3 -m venv .
    source bin/activate
    ```

    **Windows:**
    ```powershell
    python -m venv .
    .\Scripts\activate
    ```

3.  Install the required dependency:

    ```bash
    pip install plexapi
    ```

## Configuration

To connect to your Plex Server, you need your **Plex Token**.

### Option A: Environment Variables (Recommended)
Setting your token as an environment variable is more secure than typing it in the command line.

**Linux / macOS:**
```bash
export PLEX_TOKEN="your-plex-token-here"
export PLEX_URL="http://localhost:32400" # Optional, defaults to localhost
```

**Windows (PowerShell):**
```powershell
$env:PLEX_TOKEN="your-plex-token-here"
```

### Option B: Command Line Arguments
You can also pass the token directly using the `--token` flag (see usage below).

## Usage

**Important:** Before running these commands, ensure your virtual environment is active.
```bash
source bin/activate
```
*(You will see `(plex)` or similar in your terminal prompt when active).*

### 1. Basic Update (Movies)
By default, the script looks in the "Movies" library.

```bash
python update_plex_date.py --title "Piranha 3D" --date "2022-08-21"
```

### 2. Dry Run (Safety Check)
Use `--dry-run` to see if the script can find the movie and parse the date correctly, without actually writing to the Plex database.

```bash
python update_plex_date.py --title "Avatar" --date "2023-01-01" --dry-run
```

### 3. Updating TV Shows
If you want to update a show, specify the library name using `-l`.

```bash
python update_plex_date.py --library "TV Shows" --title "The Office" --date "2015-05-20"
```

### 4. Specifying Time
You can provide a specific time stamp. If omitted, it defaults to midnight (00:00:00).

```bash
python update_plex_date.py --title "Inception" --date "2020-01-01 14:30:00"
```

### Pro Tip: Running without activating
If you want to run this script simply (or via a cron job) without manually activating the environment every time, call the Python executable inside `bin/` directly:

```bash
./bin/python update_plex_date.py --title "Piranha 3D" --date "2022-08-21"
```

## Arguments Reference

| Flag | Long Flag | Required? | Description |
| :--- | :--- | :--- | :--- |
| `-t` | `--title` | **Yes** | The exact title of the item to update. |
| `-d` | `--date` | **Yes** | New date (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`). |
| `-l` | `--library` | No | Library section to search. Default: `Movies`. |
| | `--dry-run` | No | If set, no changes will be made to the server. |
| | `--token` | No | Your Plex Authentication Token (if not set in env vars). |
| | `--server` | No | Plex Server URL. Default: `http://localhost:32400`. |

## Troubleshooting

* **Item not found:** Ensure the title matches exactly as it appears in Plex. If the movie has a year in the title within Plex (e.g., "Halloween (1978)"), you must include it.
* **Unauthorized:** Your Token is likely incorrect or expired. 
* **Connection Error:** Ensure Plex is running and the `PLEX_URL` is reachable from the machine running this script.

## License

This project is open source. Feel free to modify and distribute.
