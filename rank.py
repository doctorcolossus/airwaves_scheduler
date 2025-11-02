import yaml
import random
import subprocess
import os
import sys
import re

# path where your rankings will be stored
RANKINGS_FILE = 'rankings.yaml'

# path to the text file containing the list of artists' song YouTube video IDs
ARTIST_LIST_FILE = "artist_youtube_links.txt"

def load_artists_from_file(filename):
    """
    loads a list of artists by parsing a text file with the format:
    artist name (country) [YouTube video ID]
    """

    artists = []
    # capture the three parts: name, country, video ID
    line_regex = re.compile(r'^(.+?)\s\(([^)]+)\)\s\[([^]]+)\]$')

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                match = line_regex.match(line)
                if match:
                    name, country, youtube_id = match.groups()
                    artists.append({'name':       name.strip(),
                                    'country':    country,
                                    'youtube_id': youtube_id})
                else:
                    print(f"Warning: Could not parse line {i + 1} in {filename}: '{line}'")

    except FileNotFoundError:
        print(f"Error: The input file '{filename}' was not found.")
        print("Please make sure the file exists and the ARTIST_LIST_FILE variable is set correctly.")
        return None

    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return None
        
    return artists

def load_rankings():
    """Loads existing rankings from the YAML file if it exists."""

    if not os.path.exists(RANKINGS_FILE):
        return {}

    try:
        with open(RANKINGS_FILE, 'r', encoding='utf-8') as f:
            rankings = yaml.safe_load(f)
            return rankings if rankings is not None else {}

    except Exception as e:
        print(f"Warning: Could not load or parse {RANKINGS_FILE}. Starting fresh. Error: {e}")
        return {}

def save_rankings(rankings):
    """Saves the rankings dictionary to the YAML file."""

    with open(RANKINGS_FILE, 'w', encoding='utf-8') as rankings_file:
        yaml.dump(rankings,
                  rankings_file,
                  sort_keys          = True,
                  default_flow_style = False,
                  allow_unicode      = True)

def main():

    try:
        subprocess.run(['mpv', '--version'], capture_output=True, check=True, text=True)

    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: 'mpv' command not found.")
        print("Please install mpv and ensure it's in your system's PATH.")
        sys.exit(1)

    artists = load_artists_from_file(ARTIST_LIST_FILE)

    if artists is None:
        sys.exit(1)

    rankings = load_rankings()

    print(f"Loaded {len(rankings)} existing rankings from {RANKINGS_FILE}.")

    artists_to_rank = [artist for artist in artists
                       if artist['name'] not in rankings]

    if not artists_to_rank:
        print("\nCongratulations! All artists have been ranked.")
        return

    random.shuffle(artists_to_rank)

    print(f"\nStarting ranking session for {len(artists_to_rank)} artists...")

    for i, artist in enumerate(artists_to_rank):

        artist_name = artist['name']
        artist_country = artist['country']
        youtube_id = artist['youtube_id']

        print("-" * 40)
        print(f"Artist {i + 1}/{len(artists_to_rank)}: {artist_name} ({artist_country})")

        print(f"Playing: {youtube_id}")

        if not youtube_id:
          ranking = "skipped"

        else:

            subprocess.run(['mpv', f"https://youtu.be/{youtube_id}"])

            while True:
                rank_input = input(
                    "Enter your ranking (1-10), 's' to skip, or enter to replay: "
                    ).strip().lower()

                # Replay if the user just presses Enter
                if not rank_input:
                    print("Replaying video...")
                    subprocess.run(['mpv', f"https://youtu.be/{youtube_id}"])
                    continue # Go back to the input prompt

                if rank_input == 's':
                    print(f"Skipped {artist_name}.")
                    ranking = 'skipped'
                    break

                try:
                    ranking = int(rank_input)
                    if 1 <= ranking <= 10:
                        break
                    else:
                        print("Invalid input. Please enter a number between 1 and 10.")
                except ValueError:
                    print("Invalid input. Please enter a valid number or 's'.")

        if ranking != 'skipped':
            rankings[artist_name] = ranking
            save_rankings(rankings)
            print(f"Saved ranking for {artist_name}: {ranking}")

    print("\nSession complete. All artists have now been ranked!")

if __name__ == "__main__":
    main()
