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

def parse_arguments():
    parser = argparse.ArgumentParser(description="Update the 'Added At' date for Plex items.")
    
    # Modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-t', '--title', help="Exact title of the item to update.")
    group.add_argument('--csv', help="Path to a CSV file (Format: Title,Date,Year(optional))")

    # Options
    parser.add_argument('-d', '--date', help="New date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS). Required if using -t.")
    parser.add_argument('-y', '--year', type=int, help="Year of release (for disambiguation).")
    parser.add_argument('-l', '--library', default="Movies", help="Library to search (default: Movies).")
    parser.add_argument('-i', '--interactive', action='store_true', help="Prompt user if exact match is not found.")
    
    # Connection / System
    parser.add_argument('--server', default=os.getenv('PLEX_URL', 'http://localhost:32400'), help="Plex Server URL.")
    parser.add_argument('--token', default=os.getenv('PLEX_TOKEN'), help="Plex Authentication Token.")
    parser.add_argument('--dry-run', action='store_true', help="Check for the item without making changes.")
    
    args = parser.parse_args()

    # Validation: If title is used, date is required
    if args.title and not args.date:
        parser.error("The argument --date is required when using --title.")
        
    return args

def get_plex_server(url, token):
    if not token:
        logger.error("Error: No Plex Token provided. Set PLEX_TOKEN env var or use --token.")
        sys.exit(1)
    try:
        return PlexServer(url, token)
    except Unauthorized:
        logger.error("Error: Invalid Plex Token.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: Could not connect to Plex server: {e}")
        sys.exit(1)

def parse_date(date_str):
    date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def find_item(library, title, year=None, interactive=False):
    """
    Search for an item. 
    1. Look for exact match (Title + Year).
    2. If interactive, ask user to pick from fuzzy matches.
    """
    # Broad search first
    results = library.search(title=title)
    
    # 1. Exact Filter
    matches = [x for x in results if x.title.lower() == title.lower()]
    if year:
        matches = [x for x in matches if x.year == year]

    if len(matches) == 1:
        return matches[0]
    
    # 2. Ambiguity Check (Too many exact matches)
    if len(matches) > 1:
        logger.error(f"  [!] Found {len(matches)} items matching '{title}' ({year if year else 'Any Year'}).")
        logger.error("      Please specify --year or use --interactive to select.")
        return None

    # 3. Interactive Fallback (No exact matches found)
    if interactive and results:
        print(f"\nNo exact match for '{title}'. Found these similar items:")
        for i, video in enumerate(results):
            print(f"  [{i+1}] {video.title} ({video.year})")
        
        selection = input("\nEnter number to select (or 's' to skip): ")
        if selection.isdigit() and 0 < int(selection) <= len(results):
            return results[int(selection) - 1]
    
    return None

def process_item(library, title, date_str, year=None, interactive=False, dry_run=False):
    """
    Orchestrates the finding and updating of a single item.
    """
    logger.info(f"Processing: {title}...")
    
    new_date = parse_date(date_str)
    if not new_date:
        logger.error(f"  [X] Invalid date format: '{date_str}'. Skipping.")
        return

    target = find_item(library, title, year, interactive)
    
    if not target:
        logger.error(f"  [X] Item '{title}' not found.")
        return

    # Generate Restore Command
    restore_cmd = f'python update_plex_date.py --title "{target.title}" --date "{target.addedAt}"'
    if target.year:
        restore_cmd += f' --year {target.year}'

    logger.info(f"  [+] Found: {target.title} ({target.year})")
    logger.info(f"  [+] Change: {target.addedAt} -> {new_date}")

    if dry_run:
        logger.info("  [!] Dry Run: No changes made.")
    else:
        try:
            logger.info(f"  [i] To undo, run: {restore_cmd}")
            target.edit(addedAt=new_date)
            target.reload()
            logger.info(f"  [V] Success. Date updated.")
        except Exception as e:
            logger.error(f"  [X] Update failed: {e}")
    print("-" * 40)

def process_csv(library, filepath, interactive, dry_run):
    """
    Reads a CSV and processes each row.
    Expected format: Title, Date, Year(Optional)
    """
    if not os.path.exists(filepath):
        logger.error(f"CSV file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        count = 0
        for row in reader:
            # Skip empty lines
            if not row: continue
            
            # Basic Parsing
            title = row[0].strip()
            date_str = row[1].strip()
            year = int(row[2].strip()) if len(row) > 2 and row[2].strip() else None
            
            process_item(library, title, date_str, year, interactive, dry_run)
            count += 1
    
    logger.info(f"Batch complete. Processed {count} items.")

def main():
    args = parse_arguments()
    
    plex = get_plex_server(args.server, args.token)
    try:
        library = plex.library.section(args.library)
    except NotFound:
        logger.error(f"Library '{args.library}' not found.")
        sys.exit(1)

    logger.info(f"Connected to Library: {args.library}")
    print("-" * 40)

    if args.csv:
        process_csv(library, args.csv, args.interactive, args.dry_run)
    else:
        process_item(library, args.title, args.date, args.year, args.interactive, args.dry_run)

if __name__ == "__main__":
    main()
