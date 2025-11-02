import yaml
import os
import re

RANKINGS_FILE = 'rankings.yaml'
SCHEDULE_FILE = "schedule.txt"
OUTPUT_HTML_FILE = 'schedule.html'


def parse_schedule_file(filename):
    """
    parses an indented text file and returns a structured dictionary
    Format:
      Day Name
        Time
          Artist (Venue)
    """
    schedule = {}
    current_day = None
    current_time = None
    event_regex = re.compile(r'^(.*)\s\(([^)]+)\)$')

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                indentation = len(line) - len(line.lstrip(' '))

                if indentation == 0:
                    current_day = stripped_line
                    schedule[current_day] = {}
                elif indentation == 2:
                    current_time = stripped_line
                    if current_day:
                        schedule[current_day][current_time] = []
                elif indentation >= 4:
                    if current_day and current_time:
                        match = event_regex.match(stripped_line)
                        if match:
                            artist, venue = match.groups()
                            schedule[current_day][current_time].append(
                                {'artist': artist.strip(), 'venue': venue})
                        else:
                            print("Warning: Could not parse event line "
                                  f"{i + 1}: '{stripped_line}'")

    except FileNotFoundError:
        print(f"Error: The input schedule file '{filename}' was not found.")
        return None

    except Exception as e:
        print(f"An unexpected error occurred while reading '{filename}': {e}")
        return None

    return schedule

def get_color_for_rank(rank):
    """
    generates a background and text color based on a 1-10 ranking
    interpolates from Red -> Blue -> Green
    returns a tuple of (background_hex, text_hex)
    """

    if rank is None or not isinstance(rank, (int, float)):
        return None, None

    red, green, blue = 0, 0, 0

    if rank <= 5.5: # Red to Blue
        percent = (rank - 1) / 4.5
        red, blue = 255 * (1 - percent), 255 * percent
    else: # Blue to Green
        percent = (rank - 5.5) / 4.5
        blue, green = 255 * (1 - percent), 255 * percent

    red, green, blue = int(red), int(green), int(blue)
    luminance = (0.299 * red + 0.587 * green + 0.114 * blue) / 255
    text_color = '#ffffff' if luminance < 0.5 else '#000000'
    background_color = f'#{red:02x}{green:02x}{blue:02x}'

    return background_color, text_color

def generate_html_table(schedule, rankings):
    """Generates the full HTML content for the schedule."""
    all_venues = sorted(list({
        event['venue']
        for day_events in schedule.values()
        for time_events in day_events.values()
        for event in time_events
    }))

    html_parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iceland Airwaves Ranked Schedule</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; background-color: #fdfdfd; color: #333; margin: 0; padding: 20px; }}
        h1 {{ margin-top: 0; }}
        h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 40px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 14px; margin-bottom: 30px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
        thead th {{ background-color: #f2f2f2; position: sticky; top: 0; z-index: 1; }}
        tbody tr:nth-child(even) {{ background-color: #f9f9f9; }}
        td.time-cell {{ font-weight: bold; width: 60px; }}
        .artist-cell {{ font-weight: bold; display: block; padding: 4px; margin-bottom: 2px; border-radius: 3px; }}
        ul {{ margin: 0; padding: 0; list-style-type: none; }}
    </style>
</head>
<body>
    <h1>Iceland Airwaves Ranked Schedule</h1>
"""]

    for day, day_events in schedule.items():

        html_parts.append(f'<h2>{day}</h2>')

        html_parts.append(  '<table><thead><tr><th>Time</th>'
                          + ''.join(f'<th>{venue}</th>'
                                    for venue in all_venues)
                          + '</tr></thead><tbody>')

        # treats hours 0-4 as 24-28 for sorting purposes
        time_sort_key = lambda t: (int(t.split(':')[0]) + 24
                                   if int(t.split(':')[0]) < 5
                                   else int(t.split(':')[0]))

        for time in sorted(day_events.keys(), key=time_sort_key):
            events_at_time = day_events[time]
            venue_to_events = {venue: [] for venue in all_venues}
            for event in events_at_time:
                if event['venue'] in venue_to_events:
                    venue_to_events[event['venue']].append(event['artist'])

            html_parts.append(f'<tr><td class="time-cell">{time}</td>')

            for venue in all_venues:

                artists = venue_to_events.get(venue, [])

                if artists:

                    html_parts.append('<td><ul>')

                    for artist in artists:

                        rank = rankings.get(artist)
                        background_color, text_color = get_color_for_rank(rank)

                        style = ''

                        if background_color:
                            style = f'background-color: {background_color};'
                            if text_color: # only add color if necessary
                                style += f' color: {text_color};'

                        html_parts.append(
                            f'<li><span class="artist-cell" style="{style}">'
                            f'{artist}</span></li>')

                    html_parts.append('</ul></td>')

                else:
                    html_parts.append('<td></td>')

            html_parts.append('</tr>')

        html_parts.append('</tbody></table>')

    html_parts.append("</body></html>")
    return "".join(html_parts)

def main():
    """Main function to run the process."""
    schedule_data = parse_schedule_file(SCHEDULE_FILE)
    if schedule_data is None:
        return

    print(f"Loading rankings from {RANKINGS_FILE}...")
    rankings = {}
    if os.path.exists(RANKINGS_FILE):
        with open(RANKINGS_FILE, 'r', encoding='utf-8') as f:
            rankings = yaml.safe_load(f) or {}
        print(f"Found {len(rankings)} ranked artists.")
    else:
        print(f"'{RANKINGS_FILE}' not found. No rankings will be applied.")

    print("Generating HTML schedule...")
    html_content = generate_html_table(schedule_data, rankings)

    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nSuccess! "
          f"Your personalized schedule has been saved to '{OUTPUT_HTML_FILE}'")

if __name__ == "__main__":
    main()
