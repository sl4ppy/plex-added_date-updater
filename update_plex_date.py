import os
import sys
import argparse
import logging
from datetime import datetime
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized, NotFound

# Set up logging for cleaner output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Update the 'Added At' date for a Plex item.")
    
    # Required Arguments
    parser.add_argument('-t', '--title', required=True, help="Exact title of the item to update.")
    parser.add_argument('-d', '--date', required=True, help="New date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS).")
    
    # Optional Arguments
    parser.add_argument('-l', '--library', default="Movies", help="Library to search (default: Movies).")
    parser.add_argument('--server', default=os.getenv('PLEX_URL', 'http://localhost:32400'), help="Plex Server URL.")
    parser.add_argument('--token', default=os.getenv('PLEX_TOKEN'), help="Plex Authentication Token.")
    parser.add_argument('--dry-run', action='store_true', help="Check for the item without making changes.")
    
    return parser.parse_args()

def get_plex_server(url, token):
    if not token:
        logging.error("No Plex Token provided. Set PLEX_TOKEN env var or use --token.")
        sys.exit(1)
    try:
        return PlexServer(url, token)
    except Unauthorized:
        logging.error("Invalid Plex Token.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Could not connect to Plex server: {e}")
        sys.exit(1)

def parse_date(date_str):
    """Try to parse the date string into a datetime object."""
    date_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    logging.error(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
    sys.exit(1)

def main():
    args = parse_arguments()
    
    # 1. Connect to Plex
    plex = get_plex_server(args.server, args.token)
    logging.info(f"Connected to Plex Server: {plex.friendlyName}")

    # 2. Find the Library
    try:
        library = plex.library.section(args.library)
    except NotFound:
        logging.error(f"Library '{args.library}' not found.")
        sys.exit(1)

    # 3. Find the Video
    # We use search instead of get() to handle potential near-matches or failures better
    results = library.search(title=args.title)
    
    # Filter for exact match to be safe
    target_video = next((x for x in results if x.title.lower() == args.title.lower()), None)

    if not target_video:
        logging.error(f"Could not find item '{args.title}' in library '{args.library}'.")
        sys.exit(1)

    # 4. Prepare the Update
    new_date = parse_date(args.date)
    
    logging.info(f"Found Item: {target_video.title} ({target_video.year})")
    logging.info(f"Current Added Date: {target_video.addedAt}")
    logging.info(f"New Added Date:     {new_date}")

    # 5. Execute
    if args.dry_run:
        logging.info("Dry Run enabled. No changes made.")
    else:
        try:
            # plexapi handles datetime objects directly in edit()
            target_video.edit(addedAt=new_date)
            
            # Reload to confirm
            target_video.reload()
            logging.info(f"Success! Date updated to: {target_video.addedAt}")
        except Exception as e:
            logging.error(f"Failed to update metadata: {e}")

if __name__ == "__main__":
    main()
