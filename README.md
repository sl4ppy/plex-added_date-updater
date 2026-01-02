# Plex Metadata Date Updater

A robust, user-friendly command-line tool to modify the "Date Added" metadata for items in your Plex Media Server.

This script is useful if you have migrated your Plex library, replaced file versions, or manually added content and want to preserve or correct the order in which items appear in the "Recently Added" hub.

## Features

* **Interactive Mode:** Fuzzy search helper if you don't know the exact file title.
* **Bulk Updates:** Support for processing hundreds of items at once via CSV.
* **Safety First:** "Dry Run" mode to preview changes and automatic "Undo Command" generation.
* **Precision:** optional Year filtering to handle remakes (e.g., *Halloween* 1978 vs 2007).
* **Secure:** Supports Environment Variables for credentials.

## Prerequisites

* Python 3.6+
* [PlexAPI](https://github.com/pkkid/python-plexapi)

### Installation

1.  Clone this repository.
2.  Create and activate a virtual environment (recommended):

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

3.  Install the dependency:
    ```bash
    pip install plexapi
    ```

## Configuration

Set your Plex Token as an environment variable (Recommended):

```bash
# Linux / macOS
export PLEX_TOKEN="your-token-here"
export PLEX_URL="http://localhost:32400"

# Windows Powershell
$env:PLEX_TOKEN="your-token-here"
```

*Alternatively, you can pass `--token` and `--server` as arguments to the script.*

## Usage

**Important:** Because this script relies on libraries installed in your virtual environment, you must use one of the two methods below to run it.

### Method A: Activate, then Run (Standard)
First, activate the environment so your terminal knows where to find the libraries.

```bash
source bin/activate
# You should see (plex) or similar in your prompt
python update_plex_date.py --title "Piranha 3D" --date "2022-08-21"
```

### Method B: Direct Execution (One-Liner)
You can run the script without activating the environment by pointing directly to the Python binary inside the `bin` folder.

```bash
./bin/python update_plex_date.py --title "Piranha 3D" --date "2022-08-21"
```

---

### Examples

#### 1. View Help
To see all available options and flags:

```bash
./bin/python update_plex_date.py --help
```

#### 2. Interactive Mode (Fuzzy Search)
Don't remember the exact title? Use `-i` to search and select from a list.

```bash
./bin/python update_plex_date.py --title "Star Wars" --date "1977-05-25" -i
```

#### 3. Handling Duplicates (Year)
If you have remakes (e.g., *The Mummy* 1999 vs 2017), specify the year to target the correct one.

```bash
./bin/python update_plex_date.py --title "The Mummy" --year 1999 --date "2020-01-01"
```

#### 4. Bulk Update via CSV
Update many movies at once using a CSV file.

**Create a file named `updates.csv`:**
```csv
The Matrix, 1999-03-31, 1999
Inception, 2010-07-16
Interstellar, 2014-11-07,
```
*(Format: `Title, Date, Year(Optional)`)*

**Run the script:**
```bash
./bin/python update_plex_date.py --csv updates.csv
```

## Arguments Reference

| Flag | Description |
| :--- | :--- |
| `-t`, `--title` | Exact title of the item to update. |
| `-d`, `--date` | New date (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`). |
| `--csv` | Path to a CSV file for bulk updates. |
| `-y`, `--year` | Release year (useful for remakes/duplicates). |
| `-i`, `--interactive` | Prompt user to select from partial matches if exact match fails. |
| `-l`, `--library` | Library section to search (Default: "Movies"). |
| `--dry-run` | Preview changes without modifying the database. |
| `--token` | Plex Authentication Token. |
| `--server` | Plex Server URL. |

## Undo / Restore
Every time the script runs successfully, it prints a **Restore Command** in the output.
Copy and paste that command into your terminal to revert the item to its original "Added At" date.

## Troubleshooting

* **Module not found:** You likely forgot to run `source bin/activate` or use `./bin/python`.
* **Item not found:** Try adding `-i` to search interactively.
* **Multiple items found:** Add `-y` followed by the release year to clarify which movie you mean.
* **Connection Error:** Verify `PLEX_TOKEN` and `PLEX_URL` are correct and the server is running.
