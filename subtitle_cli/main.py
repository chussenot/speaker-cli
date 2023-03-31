import click
import curses
from curses import KEY_LEFT,KEY_RIGHT,KEY_DOWN,KEY_UP
import time
import os
import signal
import subprocess


class SubtitlePlayer:
    def __init__(self, subtitles, audio_file=None):
        self.subtitles = subtitles
        self.index = 0
        self.paused = False
        self.audio_file = audio_file
        self.audio_process = None
        self.audio_paused = False
        self.update_audio_position = False

    def toggle_pause(self):
        self.paused = not self.paused
        if self.audio_process:
            self.toggle_audio()
            if not self.paused and self.update_audio_position:
                self.seek_audio(self.subtitles[self.index]["start"])
                self.update_audio_position = False

    def seek_audio(self, time):
        if self.audio_process:
            self.stop_audio()
        self.audio_process = subprocess.Popen(
            ["ffmpeg", "-ss", str(time), "-i", self.audio_file, "-f", "sndio", "default"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def play_audio(self):
        self.audio_process = subprocess.Popen(
            ["ffmpeg", "-i", self.audio_file, "-f", "sndio", "default"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_audio(self):
        if self.audio_process:
            self.audio_process.terminate()
            self.audio_process.wait()

    def pause_audio(self):
        if self.audio_process:
            os.kill(self.audio_process.pid, signal.SIGSTOP)

    def resume_audio(self):
        if self.audio_process:
            os.kill(self.audio_process.pid, signal.SIGCONT)

    def toggle_audio(self):
        if self.audio_process:
            if self.audio_paused:
                self.resume_audio()
            else:
                self.pause_audio()
            self.audio_paused = not self.audio_paused

    @property
    def current_position(self):
        return f"[{self.index + 1:03d}/{len(self.subtitles):d}]"

    def pause(self):
        self.paused = True
        if not self.audio_paused:
            os.kill(self.audio_process.pid, signal.SIGSTOP)
            self.audio_paused = True



    def toggle_pause(self):
        self.paused = not self.paused
        if self.audio_process:
            self.toggle_audio()

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
        stdscr.addstr(1, 0, f"Status: {play_status}", curses.color_pair(1))
        stdscr.refresh()

        if key == ord('q'):
            break
        elif key == KEY_LEFT:
            subtitle_player.previous()
            start_time = time.time() - subtitle["start"]
            subtitle_player.pause()
            subtitle_player.update_audio_position = True
            stdscr.clear()
            # Force display new subtitle
            stdscr.addstr(0, 0, f"{subtitle_player.current_position} {subtitle['text']}", curses.color_pair(1))
            stdscr.refresh()
        elif key == KEY_RIGHT:
            if subtitle_player.has_next():
                subtitle_player.next()
                start_time = time.time() - subtitle["start"]
                subtitle_player.pause()
                subtitle_player.update_audio_position = True
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

@click.command()
@click.argument("subtitles", type=click.Path(exists=True))
@click.option("--audio", type=click.Path(exists=True), help="Audio file to play along with subtitles")
def play(subtitles, audio):
    parsed_subtitles = parse_srt(subtitles)
    subtitle_player = SubtitlePlayer(parsed_subtitles, audio_file=audio)
    if audio:
        subtitle_player.play_audio()
    curses.wrapper(play_subtitles, subtitle_player)
    subtitle_player.stop_audio()

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
