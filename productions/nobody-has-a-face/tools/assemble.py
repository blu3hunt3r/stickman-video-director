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


SCENE_DEPS = {"s07": ["s06", "s08"]}   # scenes that import another scene's module
SCENE_LIB = {**{f"s{i:02d}": "_lib_s02_s04" for i in (2, 3, 4)}, **{f"s{i:02d}": "_lib_s05_s07" for i in (5, 6, 7)},
             **{f"s{i:02d}": "_lib_s08_s10" for i in (8, 9, 10)}, **{f"s{i:02d}": "_lib_s11_s13" for i in (11, 12, 13)},
             **{f"s{i:02d}": "_lib_s14_s15" for i in (14, 15)}, **{f"s{i:02d}": "_lib_s16_s18" for i in (16, 17, 18)}}


def _scene_ids():
    tl = json.load(open(os.path.join(ROOT, "timeline", "timeline.json")))
    return [s["id"] for s in tl["scenes"]]


def _newest(paths):
    return max((os.path.getmtime(p) for p in paths if os.path.exists(p)), default=0.0)


def _deps(sid):
    import glob
    files = glob.glob(os.path.join(ROOT, "scenes", f"{sid}_*.py"))
    if sid in SCENE_LIB:
        files.append(os.path.join(ROOT, "scenes", SCENE_LIB[sid] + ".py"))
    files += glob.glob(os.path.join(ROOT, "engine", "*.py"))
    files.append(os.path.join(ROOT, "timeline", "timeline.json"))
    for other in SCENE_DEPS.get(sid, []):
        files += glob.glob(os.path.join(ROOT, "scenes", f"{other}_*.py"))
    return files


def scene_clip(sid):
    return os.path.join(OUT, "scenes", f"{sid}.mp4")


def video(force=False, only=None):
    """Render each scene to out/scenes/sNN.mp4 (skipping up-to-date ones), then concat losslessly."""
    for sid in _scene_ids():
        if only and sid not in only:
            continue
        clip = scene_clip(sid)
        if force or not os.path.exists(clip) or os.path.getmtime(clip) < _newest(_deps(sid)):
            sh([sys.executable, "-m", "engine.render", sid, "--out", clip])
        else:
            print(f"up to date: {sid}")
    if only:
        return
    lst = os.path.join(OUT, "scenes", "concat.txt")
    with open(lst, "w") as fh:
        for sid in _scene_ids():
            fh.write(f"file '{scene_clip(sid)}'\n")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
        "-movflags", "+faststart", VIDEO])


VO_WAV = os.path.join(ROOT, "audio", "vo", "narration_full.wav")
VO_FLAC = os.path.join(ROOT, "audio", "vo", "narration_full.flac")


def audio():
    if not os.path.exists(VO_WAV) and os.path.exists(VO_FLAC):      # git stores the lossless FLAC
        sh(["ffmpeg", "-v", "error", "-y", "-i", VO_FLAC, "-c:a", "pcm_s16le", VO_WAV])
    sh([sys.executable, "-m", "audio.mix"])


# Delivery encode: the scene intermediates are CRF 15 with swscale's default BT.601 matrix and no
# colour tags; phones decode HD as BT.709, so convert + tag here (keeps the three accents exact).
COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
X264 = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-profile:v", "high", "-level", "4.2",
        "-g", "48", "-pix_fmt", "yuv420p"]
TO709 = "scale=in_color_matrix=bt601:out_color_matrix=bt709:in_range=tv:out_range=tv"


def mux(master_crf=21, social_crf=23):
    os.makedirs(FINAL, exist_ok=True)
    sh([sys.executable, "tools/captions.py"])
    meta = ["-metadata", "title=Nobody Has a Face", "-metadata", "comment=A stickman noir. Style 1 Dark, 9:16."]
    audio = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
    sh(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", TO709, *X264, "-crf", str(master_crf), *COLOR, *audio, "-shortest",
        "-movflags", "+faststart", *meta, MASTER])
    sh(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"{TO709},ass={ASS}", *X264, "-crf", str(social_crf), *COLOR, *audio, "-shortest",
        "-movflags", "+faststart", *meta, SOCIAL])
    poster()


def poster(t=79.4):
    """Thumbnail: the red umbrella reveal (S9) by default (taken from the BT.709 master)."""
    sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", MASTER, "-frames:v", "1",
        "-vf", "scale=in_color_matrix=bt709:out_color_matrix=bt709", os.path.join(FINAL, "poster.png")])


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
    if step == "scenes":                       # pre-render selected scenes: assemble.py scenes s01,s05
        video(only=sys.argv[2].split(","))
        sys.exit(0)
    steps = {"video": [video], "audio": [audio], "mux": [mux], "qa": [qa], "poster": [poster],
             "all": [video, audio, mux, qa]}[step]
    for fn in steps:
        fn()
