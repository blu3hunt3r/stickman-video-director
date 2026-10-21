"""Final assembly.

  python3 tools/assemble.py video          # render all 18 scenes -> out/video_master.mp4
  python3 tools/assemble.py audio          # run the mixer        -> out/audio_master.wav
  python3 tools/assemble.py mux            # final/nobody-has-a-face_9x16.mp4 (+ captioned cut, SRT, poster)
  python3 tools/assemble.py qa             # probe durations / frames / loudness of the finals
  python3 tools/assemble.py all            # everything in order
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
FINAL = os.path.join(ROOT, "final")
VIDEO = os.path.join(OUT, "video_master.mp4")
AUDIO = os.path.join(OUT, "audio_master.wav")
MASTER = os.path.join(FINAL, "nobody-has-a-face_9x16.mp4")
SOCIAL = os.path.join(FINAL, "nobody-has-a-face_9x16_captioned.mp4")
SRT = os.path.join(FINAL, "nobody-has-a-face.en.srt")
ASS = os.path.join(OUT, "captions_social.ass")


def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, check=True, cwd=ROOT, **kw)


def video():
    sh([sys.executable, "-m", "engine.render", "all"])


def audio():
    sh([sys.executable, "-m", "audio.mix"])


def mux():
    os.makedirs(FINAL, exist_ok=True)
    sh([sys.executable, "tools/captions.py"])
    meta = ["-metadata", "title=Nobody Has a Face", "-metadata", "comment=A stickman noir. Style 1 Dark, 9:16."]
    sh(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", *meta, MASTER])
    sh(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"ass={ASS}", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-shortest", "-movflags", "+faststart", *meta, SOCIAL])
    poster()


def poster(t=82.9):
    """Thumbnail: the red umbrella reveal (S9) by default."""
    sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", VIDEO, "-frames:v", "1",
        os.path.join(FINAL, "poster.png")])


def qa():
    for p in (VIDEO, AUDIO, MASTER, SOCIAL):
        if not os.path.exists(p):
            print("missing", p)
            continue
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration:stream=codec_name,width,height,nb_frames,r_frame_rate,sample_rate,channels",
                            "-of", "json", p], capture_output=True, text=True)
        print(os.path.basename(p), json.dumps(json.loads(r.stdout), indent=None)[:600])
    if os.path.exists(MASTER):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", MASTER, "-filter_complex",
                            "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        tail = r.stderr[r.stderr.rfind("Summary:"):]
        print(tail)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"video": [video], "audio": [audio], "mux": [mux], "qa": [qa], "poster": [poster],
             "all": [video, audio, mux, qa]}[step]
    for fn in steps:
        fn()
