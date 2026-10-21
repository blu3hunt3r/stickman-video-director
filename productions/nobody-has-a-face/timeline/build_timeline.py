"""Build the locked edit timeline from the narration word timings.

The narration was generated as ONE continuous take (voice continuity), with a
1.5 s pause between scenes. This script:
  1. splits the take into 18 scene segments on the long scene pauses,
  2. splits each segment into "pieces" wherever an internal pause is > 1.0 s and
     tightens those pauses to 0.6 s (keeps the film under the 3:00 Shorts cap),
  3. gives every scene a designed lead-in / tail (breathing room for visual beats),
  4. frame-aligns every scene at 24 fps and writes timeline.json with scene-relative
     and global word times for the animators and the sound designer.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24

# id, slug, lead-in (s before first word), tail (s after last word)
SCENES = [
    ("s01", "lineup",          0.35, 0.65),
    ("s02", "city",            0.30, 0.45),
    ("s03", "useless_evidence",0.30, 0.40),
    ("s04", "rain_murders",    0.35, 0.55),
    ("s05", "habits",          0.70, 0.85),
    ("s06", "three_oh_seven",  0.45, 1.10),
    ("s07", "left_hand",       0.35, 0.60),
    ("s08", "the_limp",        0.35, 0.60),
    ("s09", "red_umbrella",    0.50, 1.00),
    ("s10", "the_jury",        0.35, 0.60),
    ("s11", "the_chase",       0.30, 0.50),
    ("s12", "the_trap",        0.50, 0.80),
    ("s13", "blackout",        1.00, 0.60),
    ("s14", "the_mirror",      0.35, 1.40),
    ("s15", "blue_lights",     0.50, 0.50),
    ("s16", "lineup_again",    0.60, 1.30),
    ("s17", "copycat",         0.35, 0.90),
    ("s18", "verdict",         0.45, 2.20),
]
SCENE_GAP = 1.4        # pauses >= this separate scenes in the source take
TRIM_GAP_OVER = 1.0    # internal pauses longer than this get tightened...
TRIM_GAP_TO = 0.6      # ...to this
PAD_IN, PAD_OUT = 0.06, 0.12   # audio handles around each piece (cut inside silence)


def load_words():
    words = []
    with open(os.path.join(HERE, "vo_words.txt")) as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            text, a, b = line.rstrip("\n").split("\t")
            words.append({"w": text, "src0": float(a), "src1": float(b)})
    return words


def main():
    words = load_words()
    groups, cur = [], [words[0]]
    for prev, w in zip(words, words[1:]):
        if w["src0"] - prev["src1"] >= SCENE_GAP:
            groups.append(cur)
            cur = []
        cur.append(w)
    groups.append(cur)
    assert len(groups) == len(SCENES), f"expected {len(SCENES)} scene segments, got {len(groups)}"

    scenes, t_global, frame_cursor = [], 0.0, 0
    for (sid, slug, lead, tail), ws in zip(SCENES, groups):
        # split into pieces on long internal pauses
        pieces, cur = [], [ws[0]]
        for prev, w in zip(ws, ws[1:]):
            if w["src0"] - prev["src1"] > TRIM_GAP_OVER:
                pieces.append(cur)
                cur = []
            cur.append(w)
        pieces.append(cur)

        placed_words, vo_pieces = [], []
        t = lead
        for i, pw in enumerate(pieces):
            if i > 0:
                t += TRIM_GAP_TO
            offset = t - pw[0]["src0"]
            for w in pw:
                placed_words.append({"w": w["w"], "t0": round(w["src0"] + offset, 3),
                                     "t1": round(w["src1"] + offset, 3)})
            vo_pieces.append({
                "src_in": round(pw[0]["src0"] - PAD_IN, 3),
                "src_out": round(pw[-1]["src1"] + PAD_OUT, 3),
                "at": round(t - PAD_IN, 3),          # scene-relative placement of src_in
            })
            t += pw[-1]["src1"] - pw[0]["src0"]
        vo_end = t
        dur = vo_end + tail
        frames = int(round(dur * FPS))
        dur_q = frames / FPS
        start = frame_cursor / FPS
        scenes.append({
            "id": sid, "slug": slug, "index": len(scenes) + 1,
            "start": round(start, 4), "duration": round(dur_q, 4),
            "start_frame": frame_cursor, "frames": frames,
            "vo_start": round(lead, 3), "vo_end": round(vo_end, 3),
            "text": " ".join(w["w"] for w in ws),
            "vo_pieces": vo_pieces,
            "words": placed_words,
        })
        frame_cursor += frames

    total_frames = frame_cursor
    for s in scenes:
        for w in s["words"]:
            w["g0"] = round(s["start"] + w["t0"], 3)
            w["g1"] = round(s["start"] + w["t1"], 3)
        for p in s["vo_pieces"]:
            p["g_at"] = round(s["start"] + p["at"], 3)

    out = {
        "title": "Nobody Has a Face",
        "fps": FPS, "width": 1080, "height": 1920,
        "total_frames": total_frames, "total_seconds": round(total_frames / FPS, 4),
        "vo_source": {
            "provider": "Magnific / ElevenLabs Turbo v2.5", "voice": "Noah Reed (catalog)",
            "settings": {"stability": 0.5, "similarity_boost": 0.8, "speed": 0.95, "speaker_boost": True},
            "file": "audio/vo/narration_full.wav", "duration": 187.0,
        },
        "scenes": scenes,
    }
    with open(os.path.join(HERE, "timeline.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print(f"total: {total_frames} frames = {total_frames / FPS:.2f} s")
    for s in scenes:
        print(f"{s['id']} {s['slug']:<17} start {s['start']:7.3f}  dur {s['duration']:6.3f}  "
              f"frames {s['frames']:4d}  vo {s['vo_start']:.2f}-{s['vo_end']:.2f}  pieces {len(s['vo_pieces'])}")


if __name__ == "__main__":
    main()
