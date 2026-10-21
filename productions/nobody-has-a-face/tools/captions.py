"""Subtitles from the locked timeline word times.

  final/nobody-has-a-face.en.srt  - standard captions for upload (YouTube / TikTok / Reels)
  out/captions_social.ass         - styled captions + the two optional post-production
                                    overlays from the bible, for the burned-in social cut

The clean master never contains text; captions/overlays exist only in post.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_CHARS = 24          # one short line per caption (vertical video)
TITLE = ("NOBODY HAS A FACE", 8.95, 11.6)            # global seconds (S1 ring -> S2 moon)
END = ("GUILTY OR FRAMED?", 176.35, 178.83)          # final black of S18


def _words():
    tl = json.load(open(os.path.join(ROOT, "timeline", "timeline.json")))
    out = []
    for s in tl["scenes"]:
        for w in s["words"]:
            out.append(dict(w=w["w"], g0=w["g0"], g1=w["g1"], scene=s["id"]))
    # merge TTS hyphen splits: "three-" "oh-" "seven." -> "three-oh-seven."
    merged = []
    for w in out:
        if merged and merged[-1]["w"].endswith("-"):
            merged[-1]["w"] += w["w"]
            merged[-1]["g1"] = w["g1"]
        else:
            merged.append(dict(w))
    return merged, tl["total_seconds"]


WEAK_END = {"the", "a", "an", "of", "to", "in", "my", "her", "his", "their", "that", "and", "or",
            "was", "with", "on", "at", "by", "your", "you're", "i", "i'd", "i'm", "every", "one"}


def _phrases(words):
    """Split into phrases at sentence/clause punctuation and long pauses."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt["g0"] - w["g1"]) if nxt else 9.0
        if (re.search(r"[.?!,:]$", w["w"]) or w["w"].endswith("...") or gap > 0.45
                or (nxt is not None and nxt["scene"] != w["scene"])):
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
    # choose k-1 break points minimizing length variance + weak-word penalties
    import itertools
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


def chunks():
    words, total = _words()
    caps = []
    for ph in _phrases(words):
        for part in _split_balanced(ph):
            caps.append(dict(text=" ".join(x["w"] for x in part), t0=part[0]["g0"], t1=part[-1]["g1"]))
    # merge tiny one-word captions into their neighbor within the same short window
    merged = []
    for c in caps:
        if merged and (len(c["text"]) <= 7 or len(merged[-1]["text"]) <= 7) \
                and len(merged[-1]["text"]) + 1 + len(c["text"]) <= MAX_CHARS and c["t0"] - merged[-1]["t1"] < 0.5:
            merged[-1]["text"] += " " + c["text"]
            merged[-1]["t1"] = c["t1"]
        else:
            merged.append(c)
    caps = merged
    for i, c in enumerate(caps):
        c["t0"] = max(0.0, c["t0"] - 0.06)
        nxt = caps[i + 1]["t0"] - 0.06 if i + 1 < len(caps) else total
        c["t1"] = min(max(c["t1"] + 0.25, c["t0"] + 0.7), nxt - 0.02)
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


def write_srt(caps, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for i, c in enumerate(caps, 1):
            fh.write(f"{i}\n{_srt_time(c['t0'])} --> {_srt_time(c['t1'])}\n{c['text']}\n\n")


def write_ass(caps, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,1,0,1,4,2,2,90,90,470,1
Style: Title,Courier 10 Pitch,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,6,0,1,0,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as fh:
        fh.write(head)
        for c in caps:
            fh.write(f"Dialogue: 0,{_ass_time(c['t0'])},{_ass_time(c['t1'])},Cap,,0,0,0,,{c['text']}\n")
        for text, a, b in (TITLE, END):
            y = 1330 if text == TITLE[0] else 960
            fh.write(f"Dialogue: 1,{_ass_time(a)},{_ass_time(b)},Title,,0,0,0,,"
                     f"{{\\pos(540,{y})\\fad(450,450)}}{text}\n")


def main():
    caps, total = chunks()
    write_srt(caps, os.path.join(ROOT, "final", "nobody-has-a-face.en.srt"))
    write_ass(caps, os.path.join(ROOT, "out", "captions_social.ass"))
    print(f"{len(caps)} captions, film {total:.2f}s")
    for c in caps[:12]:
        print(f"  {c['t0']:7.2f}-{c['t1']:7.2f}  {c['text']}")


if __name__ == "__main__":
    main()
