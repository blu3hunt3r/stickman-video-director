"""Final assembly and delivery for one film.

  python3 tools/deliver.py --film red video      # all segments -> films/red/out/red_master.mp4
  python3 tools/deliver.py --film red audio      # films/red/audio/mix.py -> films/red/out/audio_master.wav
  python3 tools/deliver.py --film red captions   # films/red/final/red.en.srt + out/captions.ass
  python3 tools/deliver.py --film red mux        # final/red_9x16.mp4, final/red_9x16_captioned.mp4
  python3 tools/deliver.py --film red poster --t 101.5
  python3 tools/deliver.py --film red qa         # probe frames / duration / loudness of the finals
  python3 tools/deliver.py --film red all        # video, audio, captions, mux, qa

Captions exist only in post: the clean master never contains subtitle text.
"""
import argparse
import itertools
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLES = {"salvage": "SALVAGE", "shadowplay": "SHADOW PLAY", "red": "RED"}
POSTER_T = {"salvage": 160.9, "shadowplay": 126.0, "red": 77.5}     # default key frames (film s)


def P(film, *parts):
    return os.path.join(ROOT, "films", film, *parts)


def sh(cmd):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, cwd=ROOT)


def _tl(film):
    with open(P(film, "timeline", "timeline.json")) as fh:
        return json.load(fh)


# ----------------------------------------------------------------------------- video + audio
def video(film, force=False, only=None):
    cmd = [sys.executable, "-m", "engine.render", "--film", film, "all"]
    if force:
        cmd.append("--force")
    if only:
        cmd += ["--only", only]
    sh(cmd)


def audio(film):
    sh([sys.executable, P(film, "audio", "mix.py")])


# ----------------------------------------------------------------------------- captions
MAX_CHARS = 26
WEAK_END = {"the", "a", "an", "of", "to", "in", "my", "her", "his", "their", "that", "and", "or",
            "was", "with", "on", "at", "by", "your", "you're", "i", "i'd", "i'm", "every", "one", "for",
            "our", "its", "from", "as", "be", "is", "are", "were", "had", "have", "has", "been", "into", "who"}


def _words(film):
    tl = _tl(film)
    out = []
    for v in tl["vo"]:
        for w in v["words"]:
            out.append(dict(w=w["w"], g0=w["t0"], g1=w["t1"], line=v["n"]))
    return out, tl["duration"]


def _phrases(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["g0"] - w["g1"]) if nxt else 9.0
        if re.search(r"[.?!,:]$", w["w"]) or gap > 0.45 or (nxt is not None and nxt["line"] != w["line"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _split_balanced(ph):
    text = " ".join(x["w"] for x in ph)
    if len(text) <= MAX_CHARS or len(ph) < 3:
        return [ph]
    k = -(-len(text) // MAX_CHARS)
    best = None
    for cuts in itertools.combinations(range(1, len(ph)), k - 1):
        parts = [ph[a:b] for a, b in zip((0,) + cuts, cuts + (len(ph),))]
        lens = [len(" ".join(x["w"] for x in pt)) for pt in parts]
        if max(lens) > MAX_CHARS + 4 or min(len(pt) for pt in parts) < 2:
            continue
        pen = sum((L - len(text) / k) ** 2 for L in lens)
        pen += sum(400 for pt in parts[:-1] if re.sub(r"[^a-z']", "", pt[-1]["w"].lower()) in WEAK_END)
        if best is None or pen < best[0]:
            best = (pen, parts)
    return best[1] if best else [ph]


def chunks(film):
    words, total = _words(film)
    caps = []
    for ph in _phrases(words):
        for part in _split_balanced(ph):
            caps.append(dict(text=" ".join(x["w"] for x in part), t0=part[0]["g0"], t1=part[-1]["g1"],
                             line=part[0]["line"]))
    merged = []
    for c in caps:
        if merged and merged[-1]["line"] == c["line"] and (len(c["text"]) <= 7 or len(merged[-1]["text"]) <= 7) \
                and len(merged[-1]["text"]) + 1 + len(c["text"]) <= MAX_CHARS and c["t0"] - merged[-1]["t1"] < 0.5:
            merged[-1]["text"] += " " + c["text"]
            merged[-1]["t1"] = c["t1"]
        else:
            merged.append(c)
    caps = merged
    for i, c in enumerate(caps):
        c["t0"] = max(0.0, c["t0"] - 0.06)
        nxt = caps[i + 1]["t0"] - 0.06 if i + 1 < len(caps) else total
        c["t1"] = min(max(c["t1"] + 0.3, c["t0"] + 0.8), nxt - 0.02)
    return caps, total


def _srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_time(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter SemiBold,56,&H00F0F4F6,&H00F0F4F6,&H00101010,&H8C000000,0,0,0,0,100,100,0.5,0,1,3.2,1.6,2,90,90,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def captions(film):
    caps, total = chunks(film)
    os.makedirs(P(film, "final"), exist_ok=True)
    os.makedirs(P(film, "out"), exist_ok=True)
    with open(P(film, "final", f"{film}.en.srt"), "w") as fh:
        for i, c in enumerate(caps, 1):
            fh.write(f"{i}\n{_srt_time(c['t0'])} --> {_srt_time(c['t1'])}\n{c['text']}\n\n")
    with open(P(film, "out", "captions.ass"), "w") as fh:
        fh.write(ASS_HEAD)
        for c in caps:
            fh.write(f"Dialogue: 0,{_ass_time(c['t0'])},{_ass_time(c['t1'])},Cap,,0,0,0,,{{\\fad(80,120)}}{c['text']}\n")
    print(f"{film}: {len(caps)} captions over {total:.2f}s")
    return caps


# ----------------------------------------------------------------------------- mux
COLOR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
X264 = ["-c:v", "libx264", "-preset", "slow", "-tune", "grain", "-profile:v", "high", "-level", "4.2",
        "-g", "48", "-pix_fmt", "yuv420p"]
KEEP709 = "scale=in_color_matrix=bt709:out_color_matrix=bt709:in_range=tv:out_range=tv"


def mux(film, master_crf=18, social_crf=20):
    vid, aud = P(film, "out", f"{film}_master.mp4"), P(film, "out", "audio_master.wav")
    os.makedirs(P(film, "final"), exist_ok=True)
    captions(film)
    meta = ["-metadata", f"title={TITLES[film]}",
            "-metadata", "comment=Silhouette Noir trilogy. 9:16, 24 fps."]
    a = ["-c:a", "aac", "-b:a", "256k", "-ar", "48000"]
    sh(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", KEEP709, *X264, "-crf", str(master_crf), *COLOR, *a, "-shortest",
        "-movflags", "+faststart", *meta, P(film, "final", f"{film}_9x16.mp4")])
    ass = P(film, "out", "captions.ass")
    sh(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", aud, "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"{KEEP709},ass={ass}", *X264, "-crf", str(social_crf), *COLOR, *a, "-shortest",
        "-movflags", "+faststart", *meta, P(film, "final", f"{film}_9x16_captioned.mp4")])


def poster(film, t=None):
    """A full-resolution still straight from the renderer (no encode loss)."""
    sys.path.insert(0, ROOT)
    import cv2
    from engine.render import film_frame
    t = POSTER_T[film] if t is None else t
    arr = film_frame(film, t, 1.0)
    os.makedirs(P(film, "final"), exist_ok=True)
    out = P(film, "final", f"{film}_poster.png")
    cv2.imwrite(out, arr)
    print("wrote", out)


def qa(film):
    for p in (P(film, "out", f"{film}_master.mp4"), P(film, "out", "audio_master.wav"),
              P(film, "final", f"{film}_9x16.mp4"), P(film, "final", f"{film}_9x16_captioned.mp4")):
        if not os.path.exists(p):
            print("missing", p)
            continue
        r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                            "format=duration:stream=codec_name,width,height,nb_read_frames,r_frame_rate,"
                            "sample_rate,channels,color_space,color_primaries,color_transfer",
                            "-of", "json", p], capture_output=True, text=True)
        print(os.path.basename(p), json.dumps(json.loads(r.stdout))[:700])
    fin = P(film, "final", f"{film}_9x16.mp4")
    if os.path.exists(fin):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", fin, "-filter_complex",
                            "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        print(r.stderr[r.stderr.rfind("Summary:"):])
    print("timeline frames:", _tl(film)["frames"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["video", "audio", "captions", "mux", "poster", "qa", "all"])
    ap.add_argument("--film", required=True, choices=sorted(TITLES))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--t", type=float, default=None)
    a = ap.parse_args()
    f = a.film
    if a.step in ("video", "all"):
        video(f, a.force, a.only or None)
    if a.step in ("audio", "all"):
        audio(f)
    if a.step == "captions":
        captions(f)
    if a.step in ("mux", "all"):
        mux(f)
    if a.step == "poster":
        poster(f, a.t)
    if a.step in ("qa", "all"):
        qa(f)


if __name__ == "__main__":
    main()
