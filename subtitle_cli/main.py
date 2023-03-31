import click
import curses
import time

def parse_srt(subtitle_file):
    with open(subtitle_file, "r") as f:
        content = f.read()

    subtitles = []
    for subtitle in content.strip().split("\n\n"):
        index, time_range, *text_lines = subtitle.split("\n")
        start_time, end_time = time_range.split(" --> ")

        start_h, start_m, start_s = start_time.split(":")
        start_ms = int(start_s.split(",")[1])
        start_s = int(start_s.split(",")[0])

        end_h, end_m, end_s = end_time.split(":")
        end_ms = int(end_s.split(",")[1])
        end_s = int(end_s.split(",")[0])

        start = int(start_h) * 3600 + int(start_m) * 60 + start_s + start_ms / 1000
        end = int(end_h) * 3600 + int(end_m) * 60 + end_s + end_ms / 1000

        text = "\n".join(text_lines)

        subtitles.append({"start": start, "end": end, "text": text})

    return subtitles

def play_subtitles(stdscr, subtitles):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.timeout(1)

    start_time = time.time()

    for subtitle in subtitles:
        while time.time() - start_time < subtitle["start"]:
            time.sleep(0.01)

        stdscr.addstr(0, 0, subtitle["text"], curses.color_pair(1))
        stdscr.refresh()

        while time.time() - start_time < subtitle["end"]:
            time.sleep(0.01)

        stdscr.clear()

@click.command()
@click.argument("subtitles", type=click.Path(exists=True))
def cli(subtitles):
    parsed_subtitles = parse_srt(subtitles)
    curses.wrapper(play_subtitles, parsed_subtitles)

if __name__ == "__main__":
    cli()

