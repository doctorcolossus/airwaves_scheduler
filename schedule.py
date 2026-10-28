import os
import re
import yaml

RANKINGS_FILE = "rankings.yaml"
SCHEDULE_FILE = "schedule.txt"
MUSICIANS_FILE = "musicians.txt"
OUTPUT_HTML_FILE = "schedule.html"


def parse_schedule_file(
  filename: str,
) -> dict[str, dict[str, list[dict[str, str | bool]]]]:
  """parses indented schedule text file into structured dictionary"""

  schedule: dict[str, dict[str, list[dict[str, str | bool]]]] = {}

  current_day: str | None = None

  current_time: str | None = None

  event_pattern = re.compile(r"^(.*?)\s\(([^)]+)\)$")

  with open(filename, "r", encoding="utf-8") as schedule_file:

    for line_number, raw_line in enumerate(schedule_file, start=1):
      stripped_line = raw_line.strip()

      if not stripped_line:
        continue

      indentation_level = len(raw_line) - len(raw_line.lstrip(" "))

      if indentation_level == 0:
        current_day = stripped_line
        schedule[current_day] = {}

      elif indentation_level == 2:
        current_time = stripped_line

        if current_day:
          schedule[current_day][current_time] = []

      elif indentation_level >= 4:

        if current_day and current_time:

          if stripped_line.startswith("* "):
            is_selected = True
            event_text = stripped_line[2:].strip()

          else:
            is_selected = False
            event_text = stripped_line

          match = event_pattern.match(event_text)

          if not match:

            raise ValueError(
              f"Could not parse event line {line_number} in {filename}: '{stripped_line}'"
            )

          artist_name, venue_name = match.groups()

          schedule[current_day][current_time].append(
            {
              "artist":   artist_name.strip(),
              "venue":    venue_name.strip(),
              "selected": is_selected,
            }
          )

  return schedule


def parse_musicians_file(filename: str) -> dict[str, str]:
  """parses musicians file to create a lookup dictionary of artist names to URLs"""

  artist_links: dict[str, str] = {}

  line_pattern = re.compile(r"^(.+?)\s\(([^)]+)\)\s\[([^]]+)\]$")

  with open(filename, "r", encoding="utf-8") as artist_file:

    for line_number, raw_line in enumerate(artist_file, start=1):
      line = raw_line.strip()

      if not line:
        continue

      match = line_pattern.match(line)

      if not match:

        raise ValueError(
          f"Could not parse line {line_number} in {filename}: '{line}'"
        )

      artist_name, _, artist_slug = match.groups()

      artist_links[artist_name.strip()] = (
        f"https://icelandairwaves.is/artist/{artist_slug.strip()}/"
      )

  return artist_links


def generate_html_table(
  schedule:     dict[str, dict[str, list[dict[str, str | bool]]]],
  rankings:     dict[str, int],
  artist_links: dict[str, str],
) -> str:
  """generates HTML content for ranked festival schedule"""

  indentation = "    "

  navigation_items: list[str] = []

  for day in schedule.keys():
    day_identifier = day.split()[-1].lower()

    short_day_name = day_identifier[:2].capitalize()

    navigation_items.append(
      f'{indentation*3}<li>'
      f'<a href="#{day_identifier}">'
      f'<span class="full-text">{day}</span>'
      f'<span class="short-text">{short_day_name}</span>'
      f'</a>'
      f'</li>'
    )

  navigation_html = "\n".join(navigation_items)

  javascript_logic = f"""{indentation}<script>
{indentation*2}document.addEventListener("DOMContentLoaded", () => {{
{indentation*3}const navigationLinks = document.querySelectorAll(".date-navigation a");
{indentation*3}const sectionVisibleHeights = new Map();

{indentation*3}navigationLinks.forEach((link) => {{
{indentation*4}link.addEventListener("click", () => {{
{indentation*5}navigationLinks.forEach((otherLink) => otherLink.classList.remove("active"));
{indentation*5}link.classList.add("active");
{indentation*4}}});
{indentation*3}}});

{indentation*3}const thresholdSteps = Array.from({{ length: 21 }}, (_, index) => index * 0.05);

{indentation*3}const intersectionObserver = new IntersectionObserver((entries) => {{
{indentation*4}entries.forEach((entry) => {{
{indentation*5}sectionVisibleHeights.set(entry.target.id, entry.isIntersecting ? entry.intersectionRect.height : 0);
{indentation*4}}});

{indentation*4}let activeDayIdentifier = "";
{indentation*4}let maximumVisibleHeight = 0;

{indentation*4}sectionVisibleHeights.forEach((visibleHeight, dayIdentifier) => {{
{indentation*5}if (visibleHeight > maximumVisibleHeight) {{
{indentation*6}maximumVisibleHeight = visibleHeight;
{indentation*6}activeDayIdentifier = dayIdentifier;
{indentation*5}}}
{indentation*4}}});

{indentation*4}if (activeDayIdentifier) {{
{indentation*5}navigationLinks.forEach((link) => {{
{indentation*6}if (link.getAttribute("href") === "#" + activeDayIdentifier) {{
{indentation*7}link.classList.add("active");
{indentation*6}}} else {{
{indentation*7}link.classList.remove("active");
{indentation*6}}}
{indentation*5}}});
{indentation*4}}}
{indentation*3}}}, {{ root: document.querySelector(".wrapper"), rootMargin: "0px", threshold: thresholdSteps }});

{indentation*3}document.querySelectorAll(".day-section").forEach((section) => {{
{indentation*4}intersectionObserver.observe(section);
{indentation*3}}});
{indentation*2}}});
{indentation}</script>"""

  html_parts = [
    "<!DOCTYPE html>",
    "<html lang=\"en\">",
    "<head>",
    f"{indentation}<meta charset=\"UTF-8\">",
    f"{indentation}<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">",
    f"{indentation}<meta name=\"color-scheme\" content=\"light dark\">",
    f"{indentation}<title>Iceland Airwaves Ranked Schedule</title>",
    f"{indentation}<style>",
    f"{indentation*2}/* --- Base Light Mode Styles (Desktop Default) --- */",
    f"{indentation*2}html, body {{ margin: 0; padding: 0; background-color: #fdfdfd; color: #222; height: 100%; }}",
    f"{indentation*2}body {{ font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; display: flex; flex-direction: column; }}",
    f"{indentation*2}nav.date-navigation {{ padding: 20px 20px 0 20px; z-index: 100; }}",
    f"{indentation*2}nav.date-navigation ul {{ font-size: 1.5em; margin: 0; padding: 0; list-style-type: none; display: flex; gap: 20px; }}",
    f"{indentation*2}nav.date-navigation a {{ color: inherit; text-decoration: underline; }}",
    f"{indentation*2}nav.date-navigation a.active {{ color: #ff0000; text-decoration: none; }}",
    f"{indentation*2}nav.date-navigation .short-text {{ display: none; }}",
    f"{indentation*2}div.wrapper {{ overflow: auto; width: 100%; flex: 1; box-sizing: border-box; padding: 20px; -webkit-overflow-scrolling: touch; }}",
    f"{indentation*2}.day-section {{ margin-bottom: 40px; }}",
    f"{indentation*2}h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; margin-bottom: 20px; }}",
    f"{indentation*2}table {{ border-collapse: collapse; width: 100%; min-width: 900px; font-size: 14px; }}",
    f"{indentation*2}th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}",
    f"{indentation*2}span.selected {{ border: 2px solid red; }}",
    f"{indentation*2}thead th {{ background-color: #f2f2f2; position: sticky; top: 0; z-index: 10; }}",
    f"{indentation*2}tr th:nth-child(1), tr td:nth-child(1) {{ background-color: #f2f2f2; position: sticky; left: 0; z-index: 10; }}",
    f"{indentation*2}tr th:nth-child(1) {{ z-index: 20; }}",
    f"{indentation*2}tbody tr:nth-child(even) {{ background-color: #f9f9f9; }}",
    f"{indentation*2}td.time-cell {{ font-weight: bold; width: 60px; }}",
    f"{indentation*2}.artist-cell {{ font-weight: bold; display: block; padding: 4px; margin-bottom: 2px; border-radius: 3px; }}",
    f"{indentation*2}ul {{ margin: 0; padding: 0; list-style-type: none; }}",
    f"{indentation*2}.artist-cell a {{ color: inherit; text-decoration: none; }}",
    f"{indentation*2}.artist-cell a:hover {{ text-decoration: underline; }}",
    f"{indentation*2}.rank-1 {{ background-color: #ff0000; color: #ffffff; }}",
    f"{indentation*2}.rank-2 {{ background-color: #c60038; color: #ffffff; }}",
    f"{indentation*2}.rank-3 {{ background-color: #8d0071; color: #ffffff; }}",
    f"{indentation*2}.rank-4 {{ background-color: #5500aa; color: #ffffff; }}",
    f"{indentation*2}.rank-5 {{ background-color: #1c00e2; color: #ffffff; }}",
    f"{indentation*2}.rank-6 {{ background-color: #001ce2; color: #ffffff; }}",
    f"{indentation*2}.rank-7 {{ background-color: #0055aa; color: #ffffff; }}",
    f"{indentation*2}.rank-8 {{ background-color: #008d71; color: #ffffff; }}",
    f"{indentation*2}.rank-9 {{ background-color: #00c638; color: #ffffff; }}",
    f"{indentation*2}.rank-10 {{ background-color: #00ff00; color: #000000; }}",
    f"{indentation*2}/* --- Dark Mode Override --- */",
    f"{indentation*2}@media (prefers-color-scheme: dark) {{",
    f"{indentation*3}html, body {{ background-color: #1e1e1e; color: #e0e0e0; }}",
    f"{indentation*3}h2 {{ border-bottom: 2px solid #444; }}",
    f"{indentation*3}table, th, td {{ border-color: #555; }}",
    f"{indentation*3}thead th {{ background-color: #333; }}",
    f"{indentation*3}tr th:nth-child(1), tr td:nth-child(1) {{ background-color: #333; }}",
    f"{indentation*3}tbody tr:nth-child(even) {{ background-color: #2c2c2c; }}",
    f"{indentation*3}td.time-cell {{ color: #e0e0e0; }}",
    f"{indentation*3}nav.date-navigation a.active {{ color: #ff5555; }}",
    f"{indentation*2}}}",
    f"{indentation*2}/* --- 90-Degree Mobile Rotation --- */",
    f"{indentation*2}@media screen and (max-width: 1024px) {{",
    f"{indentation*3}html {{ overflow: hidden; width: 100%; height: 100%; }}",
    f"{indentation*3}body {{ flex-direction: row; position: fixed; top: 0; left: 100vw; width: 100dvh; height: 100vw; transform-origin: top left; transform: rotate(90deg); overflow: hidden; }}",
    f"{indentation*3}nav.date-navigation {{ width: 44px; height: 100%; padding: 0; background-color: #f2f2f2; border-right: 1px solid #ddd; }}",
    f"{indentation*3}nav.date-navigation ul {{ flex-direction: column; justify-content: space-around; align-items: center; height: 100%; }}",
    f"{indentation*3}nav.date-navigation .full-text {{ display: none; }}",
    f"{indentation*3}nav.date-navigation .short-text {{ display: block; font-size: 18px; font-weight: bold; }}",
    f"{indentation*3}div.wrapper {{ padding: 0; }}",
    f"{indentation*3}.day-section h2 {{ margin: 20px; }}",
    f"{indentation*3}table {{ width: max-content; min-width: 100%; border-left: none; border-right: none; }}",
    f"{indentation*2}}}",
    f"{indentation*2}@media screen and (max-width: 1024px) and (prefers-color-scheme: dark) {{",
    f"{indentation*3}nav.date-navigation {{ background-color: #1e1e1e; border-color: #444; }}",
    f"{indentation*2}}}",
    f"{indentation}</style>",
    "</head>",
    "<body>",
    f"{indentation}<nav class=\"date-navigation\">",
    f"{indentation*2}<ul>",
    navigation_html,
    f"{indentation*2}</ul>",
    f"{indentation}</nav>",
    f"{indentation}<div class=\"wrapper\">",
  ]

  for day, day_events in schedule.items():
    day_identifier = day.split()[-1].lower()

    venue_counts: dict[str, int] = {}

    for time_events in day_events.values():
      for event in time_events:
        venue_name = str(event["venue"])
        venue_counts[venue_name] = venue_counts.get(venue_name, 0) + 1

    venues_for_day = sorted(
      list(venue_counts.keys()),
      key=lambda venue: (-venue_counts[venue], venue)
    )

    if not venues_for_day:
      continue

    html_parts.append(f"\n{indentation*2}<div class=\"day-section\" id=\"{day_identifier}\">")
    html_parts.append(f"{indentation*3}<h2>{day}</h2>")
    html_parts.append(f"{indentation*3}<table>")
    html_parts.append(f"{indentation*4}<thead>")
    html_parts.append(f"{indentation*5}<tr>")
    html_parts.append(f"{indentation*6}<th>Time</th>")

    for venue in venues_for_day:
      html_parts.append(f"{indentation*6}<th>{venue}</th>")

    html_parts.append(f"{indentation*5}</tr>")
    html_parts.append(f"{indentation*4}</thead>")
    html_parts.append(f"{indentation*4}<tbody>")

    time_sort_key = lambda time_value: (
      int(time_value.split(":")[0]) + 24
      if int(time_value.split(":")[0]) < 5
      else int(time_value.split(":")[0])
    )

    for time_slot in sorted(day_events.keys(), key=time_sort_key):

      html_parts.append(f"{indentation*5}<tr>")
      html_parts.append(
        f'{indentation*6}<td class="time-cell">{time_slot}</td>'
      )

      events_at_time = day_events[time_slot]

      venue_to_events = {venue: [] for venue in venues_for_day}

      for event in events_at_time:
        if event["venue"] in venue_to_events:
          venue_to_events[event["venue"]].append(event)

      for venue in venues_for_day:

        events = venue_to_events.get(venue, [])

        if events:

          html_parts.append(f"{indentation*6}<td>")
          html_parts.append(f"{indentation*7}<ul>")

          for event in events:
            artist_name = str(event["artist"])

            is_selected = bool(event["selected"])

            rank = rankings.get(artist_name)

            rank_class = f" rank-{rank}" if rank in range(1, 11) else ""

            selected_class = " selected" if is_selected else ""

            link = artist_links.get(artist_name)

            artist_html = (
              f'<a href="{link}" target="_blank">{artist_name}</a>'
              if link
              else artist_name
            )

            html_parts.append(
              f'{indentation*8}<li><span class="artist-cell{rank_class}{selected_class}">{artist_html}</span></li>'
            )

          html_parts.append(f"{indentation*7}</ul>")
          html_parts.append(f"{indentation*6}</td>")

        else:
          html_parts.append(f"{indentation*6}<td></td>")

      html_parts.append(f"{indentation*5}</tr>")

    html_parts.append(f"{indentation*4}</tbody>")
    html_parts.append(f"{indentation*3}</table>")
    html_parts.append(f"{indentation*2}</div>")

  html_parts.append(f"{indentation}</div>")
  html_parts.append(javascript_logic)
  html_parts.append("</body>\n</html>")

  return "\n".join(html_parts)


def main() -> None:
  """generates ranked HTML schedule from text schedule and personal rankings"""

  schedule_data = parse_schedule_file(SCHEDULE_FILE)

  artist_links = parse_musicians_file(MUSICIANS_FILE)

  rankings: dict[str, int] = {}

  if os.path.exists(RANKINGS_FILE):

    with open(RANKINGS_FILE, "r", encoding="utf-8") as rankings_file:
      loaded_rankings = yaml.safe_load(rankings_file)

      if loaded_rankings:
        rankings = {
          str(name): int(score) for name, score in loaded_rankings.items()
        }

  html_content = generate_html_table(schedule_data, rankings, artist_links)

  with open(OUTPUT_HTML_FILE, "w", encoding="utf-8") as output_file:
    output_file.write(html_content)


if __name__ == "__main__":
  main()
