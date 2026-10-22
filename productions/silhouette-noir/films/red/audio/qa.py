"""RED: QA without ears.

    python3 films/red/audio/qa.py sfx [filter ...]   # previews -> films/red/out/sfx_preview/*.wav + sheet_*.png
    python3 films/red/audio/qa.py zoom NAME [key=val ...] [t0 t1]   # one sound, large sheet
    python3 films/red/audio/qa.py master [PATH]       # NaN/Inf, DC, clicks, length, LUFS, TP of the master
    python3 films/red/audio/qa.py arc                 # loudness arc table of the master, per story beat

Contact sheets: per sound, waveform (L amber, R blue, sample-peak lines) + log-frequency
spectrogram, labelled with length, sample peak, true peak, max momentary loudness, DC.
"""
from __future__ import annotations

import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    __package__ = "films.red.audio"

import numpy as np  # noqa: E402

from films.red.audio import common  # noqa: E402
from audio import dsp  # noqa: E402

OUT = common.OUT
PREVIEW = os.path.join(OUT, "sfx_preview")


def stats(x):
    y = dsp.pad_to(x, max(len(x), dsp.n_of(0.4)))
    return dict(len_s=round(len(x) / dsp.SR, 3), peak_db=round(dsp.sample_peak_db(x), 2), tp_db=round(dsp.true_peak_db(x), 2),
                dc=float(np.mean(x)), max_m=round(float(np.max(dsp.loudness_curve(y, win=0.4, hop=0.05)[1])), 2),
                finite=bool(np.isfinite(x).all()))


def _spec(x, nfft=1024, hop=256):
    m = dsp.mono(x)
    if len(m) < nfft:
        m = np.pad(m, (0, nfft - len(m)))
    win = np.hanning(nfft)
    frames = 1 + (len(m) - nfft) // hop
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    S = np.abs(np.fft.rfft(m[idx] * win, axis=1)) + 1e-9
    S = 20 * np.log10(S / S.max())
    f = np.fft.rfftfreq(nfft, 1 / dsp.SR)
    t = (np.arange(frames) * hop + nfft / 2) / dsp.SR
    return t, f, S.T


def sheets(items, prefix, per=12, cols=4, scale=1.0, outdir=PREVIEW):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    for si in range(0, len(items), per):
        chunk = items[si:si + per]
        rows = (len(chunk) + cols - 1) // cols
        fig = plt.figure(figsize=(cols * 4.4 * scale, rows * 3.4 * scale), dpi=72)
        fig.patch.set_facecolor("#111")
        gs = fig.add_gridspec(rows * 2, cols, height_ratios=[1, 1.4] * rows, hspace=0.6, wspace=0.18)
        for k, (label, x, st) in enumerate(chunk):
            r, c = divmod(k, cols)
            ax = fig.add_subplot(gs[2 * r, c])
            t = np.arange(len(x)) / dsp.SR
            step = max(1, len(x) // 4000)
            ax.plot(t[::step], x[::step, 0], lw=0.5, color="#f0b050")
            ax.plot(t[::step], x[::step, 1], lw=0.4, color="#5090ff", alpha=0.6)
            pk = 10 ** (st["peak_db"] / 20)
            ax.axhline(pk, color="#c33", lw=0.5)
            ax.axhline(-pk, color="#c33", lw=0.5)
            ax.set_xlim(0, max(t[-1] if len(t) else 0.05, 0.05))
            ax.set_facecolor("#000")
            ax.tick_params(colors="#aaa", labelsize=6)
            ax.set_title(f"{label}\n{st['len_s']:.2f}s pk {st['peak_db']:.1f} TP {st['tp_db']:.1f} M {st['max_m']:.1f} dc {st['dc']:+.4f}",
                         color="#eee", fontsize=7)
            ax2 = fig.add_subplot(gs[2 * r + 1, c])
            ts, fs, S = _spec(x)
            ax2.pcolormesh(ts, np.maximum(fs, 1.0), S, vmin=-90, vmax=0, cmap="magma", shading="auto")
            ax2.set_yscale("log")
            ax2.set_ylim(30, 20000)
            ax2.tick_params(colors="#aaa", labelsize=6)
        p = os.path.join(outdir, f"{prefix}_{si // per + 1:02d}.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fig.savefig(p, facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(p)
    return paths


def run_sfx(filters=None):
    from films.red.audio import sfx_red
    os.makedirs(PREVIEW, exist_ok=True)
    items, report = [], {}
    seen = {}
    for name, prm in sfx_red.PREVIEWS:
        prm = dict(prm)
        dur = prm.pop("_dur", None)
        label = name + ("" if not prm else "_" + "_".join(f"{k}{v}" for k, v in prm.items()))
        if filters and not any(f in label for f in filters):
            continue
        seen[label] = seen.get(label, 0) + 1
        x, sync = sfx_red.render_sync(name, dur=dur, params=prm, seed=1)
        st = stats(x)
        st["sync"] = sync
        report[label] = st
        y = x * min(1.0, 10 ** (-1.0 / 20) / max(1e-9, float(np.max(np.abs(x)))))
        dsp.write_wav(os.path.join(PREVIEW, f"{label}.wav"), y, bits=24)
        items.append((label, x, st))
    # seed variation check: two takes of the same sound must differ
    a = sfx_red.render("snow_step", seed=1)
    b = sfx_red.render("snow_step", seed=2)
    report["_seed_variation_snow_step"] = bool(len(a) != len(b) or not np.allclose(a, b))
    c = sfx_red.render("snow_step", seed=1)
    report["_deterministic_snow_step"] = bool(np.array_equal(a, c))
    prefix = "sheet" if not filters else "sheet_" + "_".join(filters)[:40]
    paths = sheets(items, prefix)
    with open(os.path.join(PREVIEW, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    bad = [k for k, v in report.items() if isinstance(v, dict) and (not v["finite"] or abs(v["dc"]) > 1e-3 or v["tp_db"] > -0.9)]
    print(f"{len(items)} previews -> {PREVIEW}; problems: {bad or 'none'}; "
          f"seed variation {report['_seed_variation_snow_step']}, deterministic {report['_deterministic_snow_step']}")
    for p in paths:
        print(p)
    return paths


# ---------------------------------------------------------------------------- master checks
def find_clicks(x, sr=dsp.SR, thresh=8.0, max_report=20):
    """Sample-discontinuity detector: 2nd difference of the 7 kHz-high-passed signal vs its local
    (20 ms) RMS; events above thresh x local and an absolute floor."""
    hp = dsp.sos(np.asarray(x, dtype=np.float64), "highpass", 7000.0, 4)
    d2 = np.abs(np.diff(hp, n=2, axis=0)).max(axis=1)
    w = dsp.n_of(0.02, sr)
    c = np.concatenate([[0.0], np.cumsum(d2 ** 2)])
    i = np.arange(len(d2))
    lo, hi = np.maximum(0, i - w), np.minimum(len(d2), i + w)
    local = np.sqrt((c[hi] - c[lo]) / np.maximum(hi - lo, 1))
    score = d2 / (local + 1e-6)
    cand = np.nonzero((score > thresh) & (d2 > 10 ** (-50 / 20)))[0]
    events, last = [], -10 ** 9
    for k in cand:
        if k - last > sr * 0.05:
            events.append(k)
        last = k
    events = sorted(events, key=lambda k: -score[k])[:max_report]
    return [dict(t=round((k + 1) / sr, 4), score=round(float(score[k]), 1), level_db=round(float(dsp.lin2db(d2[k])), 1))
            for k in sorted(events)]


def check_master(x, sr=dsp.SR, expect_n=None):
    res = dict(samples=int(len(x)), seconds=len(x) / sr)
    if expect_n is not None:
        res["length_ok"] = int(len(x)) == int(expect_n)
    res["finite"] = bool(np.isfinite(x).all())
    res["dc_offset"] = [round(float(v), 6) for v in np.mean(x, axis=0)]
    res["integrated_lufs"] = round(dsp.loudness_integrated(x, sr), 2)
    res["true_peak_dbtp"] = round(dsp.true_peak_db(x), 2)
    res["sample_peak_dbfs"] = round(dsp.sample_peak_db(x), 2)
    _, st = dsp.loudness_curve(x, sr, win=3.0, hop=0.5)
    res["lra_approx_lu"] = round(float(np.percentile(st[st > -70], 95) - np.percentile(st[st > -70], 10)), 1) if np.any(st > -70) else None
    res["clicks"] = find_clicks(x, sr)
    return res


# story beats for the loudness-arc table (film seconds)
ARC = [
    ("hook: the rule (music box)", 0.0, 9.0),
    ("the hood, doors close", 9.0, 24.0),
    ("descent (title, path)", 24.0, 34.3),
    ("THE SILENCE (after the voice)", 36.3, 37.3),
    ("the wolf appears", 38.5, 44.4),
    ("the chase", 44.5, 57.2),
    ("fall / stop / wait", 57.2, 66.5),
    ("red hoods", 66.5, 81.0),
    ("Grandmother (dread)", 81.0, 87.4),
    ("the charge", 87.4, 94.0),
    ("the fight", 94.0, 97.0),
    ("basket / lantern", 97.0, 106.6),
    ("FIRE", 106.6, 111.0),
    ("dawn", 111.5, 125.0),
    ("the cold village", 125.0, 133.3),
    ("the embrace", 133.3, 139.0),
    ("warm end", 139.0, 154.0),
]


def arc_table(x, sr=dsp.SR):
    t, lm = dsp.loudness_curve(x, sr, win=0.4, hop=0.1)
    ts, ls = dsp.loudness_curve(x, sr, win=3.0, hop=0.1)
    rows = []
    for label, a, b in ARC:
        m = (t >= a) & (t <= b)
        ms = (ts >= a + 1.0) & (ts <= b - 1.0) if b - a > 3 else (ts >= a) & (ts <= b)
        seg = x[dsp.n_of(a):dsp.n_of(b)]
        lv = dsp.loudness_integrated(seg) if len(seg) > dsp.n_of(0.5) else -np.inf
        rows.append(dict(beat=label, t0=a, t1=b, lufs=round(float(lv), 1) if np.isfinite(lv) else None,
                         momentary_max=round(float(np.max(lm[m])), 1) if m.any() else None,
                         short_term_max=round(float(np.max(ls[ms])), 1) if ms.any() else None,
                         rms_db=round(dsp.rms_db(seg), 1)))
    return rows


def overview(master, stems, path, events=None, title="RED - loudness overview"):
    """Short-term (3 s) + momentary (0.4 s) loudness of the master, stems short-term, scene
    boundaries + labels, hit / designed-silence markers."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(24, 10), dpi=72, gridspec_kw=dict(height_ratios=[2.3, 1]))
    fig.patch.set_facecolor("#111")
    ax = axes[0]
    tm, lm = dsp.loudness_curve(master, win=0.4, hop=0.05)
    ts, ls = dsp.loudness_curve(master, win=3.0, hop=0.1)
    ax.plot(tm, lm, color="#777", lw=0.6, label="master momentary (0.4 s)")
    ax.plot(ts, ls, color="#f0b050", lw=1.8, label="master short-term (3 s)")
    colors = dict(vo="#ffffff", music="#5090ff", sfx="#e04050", amb="#40c080")
    for k, x in stems.items():
        if x is None or not np.any(x):
            continue
        t2, l2 = dsp.loudness_curve(x, win=3.0, hop=0.1)
        axes[1].plot(t2, l2, lw=1.0, color=colors.get(k, "#ccc"), label=f"{k} short-term")
    integ = dsp.loudness_integrated(master)
    ax.axhline(integ, color="#f0b050", lw=0.6, ls="--")
    ax.text(1, integ + 0.6, f"integrated {integ:.1f} LUFS", color="#f0b050", fontsize=9)
    for a in axes:
        for s in common.TL["scenes"]:
            a.axvline(s["start"], color="#555", lw=0.9)
        a.set_facecolor("#000")
        a.tick_params(colors="#bbb")
        a.set_xlim(0, len(master) / dsp.SR)
        a.set_xticks(np.arange(0, len(master) / dsp.SR + 1, 5))
        a.grid(color="#222")
    for s in common.TL["scenes"]:
        ax.text(s["start"] + 0.2, -5, s["id"], color="#ddd", fontsize=9)
        ax.text(s["start"] + 0.2, -8, s["slug"][:12], color="#999", fontsize=7)
    for i, ev in enumerate(events or []):
        ax.axvline(ev["t"], color=ev.get("color", "#c33"), lw=0.6, ls=":")
        ax.text(ev["t"] + 0.05, -66 + 4.5 * (i % 5), ev["label"], color=ev.get("color", "#c33"), fontsize=6.5, rotation=90,
                va="bottom")
    ax.set_ylim(-68, -2)
    axes[1].set_ylim(-75, -5)
    ax.set_ylabel("LUFS", color="#bbb")
    axes[1].set_ylabel("stems LUFS (3 s)", color="#bbb")
    axes[1].set_xlabel("film seconds", color="#bbb")
    ax.legend(loc="lower right", facecolor="#222", labelcolor="#ddd", fontsize=8)
    axes[1].legend(loc="lower right", facecolor="#222", labelcolor="#ddd", fontsize=8, ncol=4)
    ax.set_title(title, color="#eee")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "sfx"
    if cmd == "sfx":
        run_sfx(argv[2:] or None)
    elif cmd == "zoom":
        from films.red.audio import sfx_red
        name = argv[2]
        rest = argv[3:]
        nums = [float(v) for v in rest if v.replace(".", "", 1).isdigit()][:2]
        prm = {}
        for kv in rest:
            if "=" in kv:
                k, v = kv.split("=", 1)
                try:
                    prm[k] = float(v)
                except ValueError:
                    prm[k] = v
        dur = prm.pop("dur", None)
        seed = int(prm.pop("seed", 1))
        x = sfx_red.render(name, dur=dur, params=prm or None, seed=seed)
        if len(nums) == 2:
            x = x[dsp.n_of(nums[0]):dsp.n_of(nums[1])]
        p = sheets([(name + " " + " ".join(rest), x, stats(x))], f"zoom_{name}", per=1, cols=1, scale=3.0)
        print(p[0])
    elif cmd == "master":
        path = argv[2] if len(argv) > 2 else os.path.join(OUT, "audio_master.wav")
        x, sr = dsp.read_audio(path)
        print(json.dumps(check_master(x, sr, common.N), indent=1))
    elif cmd == "arc":
        path = argv[2] if len(argv) > 2 else os.path.join(OUT, "audio_master.wav")
        x, sr = dsp.read_audio(path)
        for r in arc_table(x, sr):
            print(f"{r['beat']:<28} {r['t0']:6.1f}-{r['t1']:6.1f}  LUFS {r['lufs']!s:>6}  Mmax {r['momentary_max']!s:>6}  "
                  f"Smax {r['short_term_max']!s:>6}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
