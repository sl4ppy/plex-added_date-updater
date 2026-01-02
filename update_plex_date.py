import os
import sys
import argparse
import logging
import csv
from datetime import datetime
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized, NotFound

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

# ANSI Colors for the interactive menu
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Update the 'Added At' date for Plex items.")
    
    # Modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--title', help="Title to search for.")
    group.add_argument('--csv', help="Path to a CSV file (Format: Title,Date,Year(optional))")

    # Options
    parser.add_argument('-d', '--date', help="New date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS). Required if using -t.")
    parser.add_argument('-y', '--year', type=int, help="Year of release (optional filter).")
    parser.add_argument('-l', '--library', default="Movies", help="Library to search (default: Movies).")
    parser.add_argument('-i', '--interactive', action='store_true', help="Show a list of all matching results to select from.")
    
    # Connection / System
    parser.add_argument('--server', default=os.getenv('PLEX_URL', 'http://localhost:32400'), help="Plex Server URL.")
    parser.add_argument('--token', default=os.getenv('PLEX_TOKEN'), help="Plex Authentication Token.")
    parser.add_argument('--dry-run', action='store_true', help="Check for the item without making changes.")
    
    args = parser.parse_args()

    # Validation
    if args.title and not args.date:
        parser.error("The argument --date is required when using --title.")
        
    return args

def get_plex_server(url, token):
    if not token:
        logger.error(f"{RED}Error:{RESET} No Plex Token provided. Set PLEX_TOKEN env var or use --token.")
        sys.exit(1)
    try:
        return PlexServer(url, token)
    except Unauthorized:
        logger.error(f"{RED}Error:{RESET} Invalid Plex Token.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{RED}Error:{RESET} Could not connect to Plex server: {e}")
        sys.exit(1)

def parse_date(date_str):
    date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def select_interactively(results, title_query):
    """
    Displays a table of results and prompts the user to select one.
    """
    print(f"\n--- {CYAN}SEARCH RESULTS FOR '{title_query}'{RESET} ---")
    print(f"{'ID':<4} {'YEAR':<6} {'CURRENT ADDED DATE':<22} {'TITLE'}")
    print("-" * 80)

    for idx, item in enumerate(results):
        # highlight exact matches in Green, others in White
        color = RESET
        if item.title.lower() == title_query.lower():
            color = GREEN
        
        row_id = idx + 1
        added_str = str(item.addedAt)[:19] # Truncate microseconds
        print(f"{color}{row_id:<4} {item.year:<6} {added_str:<22} {item.title}{RESET}")

    print("-" * 80)
    selection = input(f"\n{YELLOW}Select ID (or Enter to quit): {RESET}").strip()

    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(results):
            return results[idx]
    
    print("No selection made. Exiting.")
    sys.exit(0)

def find_item(library, title, year=None, interactive=False):
    # 1. Search Plex (returns partial matches too)
    results = library.search(title=title)
    
    if not results:
        return None

    # 2. If Year is provided, filter rigidly (unless interactive)
    if year:
        # If interactive, we just highlight or sort, but we usually want to filter
        # But to be robust, let's filter, and if 0 left, warn user.
        filtered = [x for x in results if x.year == year]
        if not filtered and not interactive:
            return None
        if filtered:
            results = filtered

    # 3. INTERACTIVE MODE: Always show the list if requested OR if ambiguous
    # Check for ambiguity (multiple exact matches or multiple results in general)
    exact_matches = [x for x in results if x.title.lower() == title.lower()]
    
    # Trigger interactive menu if:
    # A) User passed -i
    # B) There are multiple exact matches (e.g. Star Wars)
    # C) There are NO exact matches, but we have partials (e.g. Typo)
    should_prompt = interactive or len(exact_matches) > 1 or (not exact_matches and len(results) > 0)

    if should_prompt:
        return select_interactively(results, title)

    # 4. Automatic Mode (Single Exact Match)
    if len(exact_matches) == 1:
        return exact_matches[0]

    return None

def process_item(library, title, date_str, year=None, interactive=False, dry_run=False):
    logger.info(f"Searching for: {title}...")
    
    target = find_item(library, title, year, interactive)
    
    if not target:
        logger.error(f"{RED}  [X] Item '{title}' not found.{RESET}")
        return

    new_date = parse_date(date_str)
    if not new_date:
        logger.error(f"{RED}  [X] Invalid date format: '{date_str}'.{RESET}")
        return

    # Generate Restore Command
    restore_cmd = f'python update_plex_date.py --title "{target.title}" --date "{target.addedAt}"'
    if target.year:
        restore_cmd += f' --year {target.year}'

    print(f"\n{GREEN}SELECTED ITEM:{RESET} {target.title} ({target.year})")
    print(f"Old Date: {target.addedAt}")
    print(f"New Date: {CYAN}{new_date}{RESET}")

    if dry_run:
        print(f"\n{YELLOW}[DRY RUN] No changes made.{RESET}")
    else:
        try:
            target.edit(addedAt=new_date)
            target.reload()
            print(f"{GREEN}[SUCCESS] Date updated.{RESET}")
            print(f"Undo Command: {restore_cmd}")
        except Exception as e:
            logger.error(f"{RED}Update failed: {e}{RESET}")
    print("-" * 60)

def process_csv(library, filepath, interactive, dry_run):
    if not os.path.exists(filepath):
        logger.error(f"CSV file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            title = row[0].strip()
            date_str = row[1].strip()
            year = int(row[2].strip()) if len(row) > 2 and row[2].strip() else None
            
            # For CSV, we generally don't want interactive unless specifically asked
            process_item(library, title, date_str, year, interactive, dry_run)

def main():
    args = parse_arguments()
    
    plex = get_plex_server(args.server, args.token)
    try:
        library = plex.library.section(args.library)
    except NotFound:
        logger.error(f"{RED}Library '{args.library}' not found.{RESET}")
        sys.exit(1)

    if args.csv:
        process_csv(library, args.csv, args.interactive, args.dry_run)
    else:
        process_item(library, args.title, args.date, args.year, args.interactive, args.dry_run)

if __name__ == "__main__":
    main()
