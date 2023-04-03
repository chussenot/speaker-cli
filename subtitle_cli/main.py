import click
import curses
import time
import os
import signal
import subprocess

KEY_LEFT, KEY_RIGHT, KEY_DOWN, KEY_UP = curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_DOWN, curses.KEY_UP

class SubtitlePlayer:
    def __init__(self, subtitles, audio_file=None):
        self.subtitles, self.index, self.paused, self.audio_file = subtitles, 0, False, audio_file
        self.audio_process, self.audio_paused, self.update_audio_position = None, False, False

    def toggle_pause(self):
        self.paused = not self.paused
        self.toggle_audio()

    def play_audio(self, time='00:00:00'):
        if self.audio_process: self.stop_audio()
        time = self.get_current()["start_time"]
        self.audio_process = subprocess.Popen(["ffmpeg", "-ss", time, "-i", self.audio_file, "-f", "sndio", "default"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop_audio(self):
        if self.audio_process: self.audio_process.terminate(), self.audio_process.wait()

    def pause_audio(self):
        if self.audio_process: os.kill(self.audio_process.pid, signal.SIGSTOP)

    def resume_audio(self):
        if self.audio_process: os.kill(self.audio_process.pid, signal.SIGCONT)

    def toggle_audio(self):
        if self.audio_process:
            self.resume_audio() if self.audio_paused else self.pause_audio()
            self.audio_paused = not self.audio_paused

    @property
    def current_position(self): return f"[{self.index + 1:03d}/{len(self.subtitles):d}]"

    def pause(self):
        self.paused = True
        if not self.audio_paused: os.kill(self.audio_process.pid, signal.SIGSTOP), setattr(self, "audio_paused", True)

    def previous(self):
        if self.index > 0: self.index -= 1

    def has_next(self): return self.index < len(self.subtitles) - 1

    def next(self):
        if self.has_next(): self.index += 1

    def get_current(self): return self.subtitles[self.index]

def parse_srt(subtitle_file):
    with open(subtitle_file, "r") as f: content = f.read()
    subtitles = []
    for subtitle in content.strip().split("\n\n"):
        index, time_range, *text_lines = subtitle.split("\n")
        start_time, end_time = time_range.split(" --> ")
        start_h, start_m, start_s, end_h, end_m, end_s = *start_time.split(":"), *end_time.split(":")
        start_ms, end_ms, start_s, end_s = int(start_s.split(",")[1]), int(end_s.split(",")[1]), int(start_s.split(",")[0]), int(end_s.split(",")[0])
        start, end = int(start_h) * 3600 + int(start_m) * 60 + start_s + start_ms / 1000, int(end_h) * 3600 + int(end_m) * 60 + end_s + end_ms / 1000
        text = "\n".join(text_lines)
        subtitles.append({"start_time": start_time.split(",")[0], "start": start, "end": end, "text": text})
    return subtitles

def play_subtitles(stdscr, subtitle_player):
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK), stdscr.timeout(100), stdscr.nodelay(True), curses.curs_set(


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
        subtitle_player.play_audio('00:00:00')
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
