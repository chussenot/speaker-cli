import click
import curses
from curses import KEY_LEFT,KEY_RIGHT,KEY_DOWN,KEY_UP
import time


class SubtitlePlayer:
    def __init__(self, subtitles):
        self.subtitles = subtitles
        self.index = 0
        self.paused = False

    @property
    def current_position(self):
        return f"[{self.index + 1:03d}/{len(self.subtitles):d}]"

    def pause(self):
        self.paused = True

    def toggle_pause(self):
        self.paused = not self.paused

    def previous(self):
        if self.index > 0:
            self.index -= 1

    def has_next(self):
        return self.index < len(self.subtitles) - 1

    def next(self):
        if self.has_next():
            self.index += 1

    def get_current(self):
        return self.subtitles[self.index]

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

def play_subtitles(stdscr, subtitle_player):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    stdscr.timeout(100)
    stdscr.nodelay(True)
    curses.curs_set(0)

    start_time = time.time()
    paused_time = 0
    key_display_time = 0

    while True:
        subtitle = subtitle_player.get_current()
        elapsed_time = time.time() - start_time

        if not subtitle_player.paused:
            if elapsed_time >= subtitle["start"] and elapsed_time <= subtitle["end"]:
                # stdscr.addstr(0, 0, subtitle["text"], curses.color_pair(1))
                stdscr.addstr(0, 0, f"{subtitle_player.current_position} {subtitle['text']}", curses.color_pair(1))

                stdscr.refresh()

            elif elapsed_time > subtitle["end"]:
                stdscr.clear()
                if subtitle_player.has_next():
                    subtitle_player.next()
                else:
                    break

        key = stdscr.getch()
        if time.time() - key_display_time > 1:
            stdscr.addstr(2, 0, " " * 20, curses.color_pair(1))
            stdscr.refresh()

        play_status = "Playing" if not subtitle_player.paused else "Paused  "
        stdscr.addstr(3, 0, f"Status: {play_status}", curses.color_pair(1))
        stdscr.refresh()

        if key == ord('q'):
            break
        elif key == KEY_LEFT:
            subtitle_player.previous()
            start_time = time.time() - subtitle["start"]
            subtitle_player.pause()
            stdscr.clear()
            # Force display new subtitle
            stdscr.addstr(0, 0, f"{subtitle_player.current_position} {subtitle['text']}", curses.color_pair(1))
            stdscr.refresh()
        elif key == KEY_RIGHT:
            if subtitle_player.has_next():
                subtitle_player.next()
                start_time = time.time() - subtitle["start"]
                subtitle_player.pause()
            stdscr.clear()
            # Force display new subtitle
            stdscr.addstr(0, 0, f"{subtitle_player.current_position} {subtitle['text']}", curses.color_pair(1))
            stdscr.refresh()
        elif key == ord(' '):
            subtitle_player.toggle_pause()
            if subtitle_player.paused:
                paused_time = time.time()
            else:
                start_time += time.time() - paused_time
                paused_time = 0

        if key != -1:
            stdscr.addstr(2, 0, f"Pressed key: {chr(key) if key != ord(' ') else '<SPACE>'}", curses.color_pair(1))
            stdscr.refresh()
            key_display_time = time.time()



@click.group()
def cli():
    pass

@cli.command()
@click.argument("subtitles", type=click.Path(exists=True))
def play(subtitles):
    parsed_subtitles = parse_srt(subtitles)
    subtitle_player = SubtitlePlayer(parsed_subtitles)
    curses.wrapper(play_subtitles, subtitle_player)

@click.command()
def help():
    click.echo("Subtitle CLI - Keybindings:")
    click.echo("  KEY_LEFT   - Previous subtitle")
    click.echo("  KEY_RIGHT  - Next subtitle")
    click.echo("  SPACE      - Toggle play/pause")
    click.echo("  q          - Quit playback")

cli.add_command(play, name="play")
cli.add_command(help, name="help")

if __name__ == "__main__":
    cli()
