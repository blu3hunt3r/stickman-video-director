"""QA without ears.

    python3 -m audio.qa sfx            # every SFX (+ key variants) -> out/sfx_preview/<name>.wav + sheet_*.png
    python3 -m audio.qa master [PATH]  # checks out/audio_master.wav (NaN/Inf, DC, clicks, length, LUFS, TP)
    python3 -m audio.qa overview       # out/audio_overview.png: loudness curve + scene boundaries + stems

Contact sheets show, per sound: waveform (with the sample-peak line) and a log-frequency
spectrogram, labelled with length, peak, true peak, DC and max momentary loudness.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from . import dsp, sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")

# variants rendered in addition to every catalog name at its defaults
VARIANTS = [
    ("footstep", dict(params=dict(weight=0.35, wet=0)), "footstep_w0.35_dry"),
    ("footstep", dict(params=dict(weight=1.0, wet=0)), "footstep_w1.0_dry"),
    ("footstep", dict(params=dict(weight=0.35, wet=1)), "footstep_w0.35_wet"),
    ("footstep", dict(params=dict(weight=1.0, wet=1)), "footstep_w1.0_wet"),
    ("thunder", dict(params=dict(distance=0.0)), "thunder_d0"),
    ("thunder", dict(params=dict(distance=1.0)), "thunder_d1"),
    ("impact", dict(params=dict(size=1.0)), "impact_s1"),
    ("impact", dict(params=dict(size=0.2)), "impact_s0.2"),
    ("whoosh", dict(params=dict(size=1.0)), "whoosh_s1"),
    ("bell_toll", dict(params=dict(count=3)), "bell_toll_x3"),
    ("heartbeat", dict(dur=6.0, params=dict(bpm=66, bpm_end=96)), "heartbeat_ramp"),
    ("bulb_hum", dict(dur=1.0), "bulb_hum_1s_cut"),
]


def _stats(x):
    return dict(len_s=len(x) / dsp.SR, peak_db=dsp.sample_peak_db(x), tp_db=dsp.true_peak_db(x),
                dc=float(np.mean(x)), max_m=float(np.max(dsp.loudness_curve(dsp.pad_to(x, max(len(x), dsp.n_of(0.4))), win=0.4, hop=0.05)[1])),
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


def sheets(items, prefix, per=16, cols=4, scale=1.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    for si in range(0, len(items), per):
        chunk = items[si:si + per]
        rows = (len(chunk) + cols - 1) // cols
        fig = plt.figure(figsize=(cols * 4.2 * scale, rows * 3.3 * scale), dpi=80)
        fig.patch.set_facecolor("#111")
        gs = fig.add_gridspec(rows * 2, cols, height_ratios=[1, 1.4] * rows, hspace=0.55, wspace=0.18)
        for k, (label, x, st) in enumerate(chunk):
            r, c = divmod(k, cols)
            ax = fig.add_subplot(gs[2 * r, c])
            t = np.arange(len(x)) / dsp.SR
            step = max(1, len(x) // 4000)
            ax.plot(t[::step], x[::step, 0], lw=0.5, color="#f0b050")
            if x.shape[1] > 1:
                ax.plot(t[::step], x[::step, 1], lw=0.4, color="#5090ff", alpha=0.6)
            pk = 10 ** (st["peak_db"] / 20)
            ax.axhline(pk, color="#c33", lw=0.5)
            ax.axhline(-pk, color="#c33", lw=0.5)
            ax.set_xlim(0, max(t[-1], 0.05))
            ax.set_facecolor("#000")
            ax.tick_params(colors="#aaa", labelsize=6)
            ax.set_title(f"{label}  {st['len_s']:.2f}s  pk {st['peak_db']:.1f}  TP {st['tp_db']:.1f}  "
                         f"Mmax {st['max_m']:.1f}  dc {st['dc']:+.4f}", color="#eee", fontsize=7)
            ax2 = fig.add_subplot(gs[2 * r + 1, c])
            ts, fs, S = _spec(x)
            ax2.pcolormesh(ts, np.maximum(fs, 1.0), S, vmin=-90, vmax=0, cmap="magma", shading="auto")
            ax2.set_yscale("log")
            ax2.set_ylim(25, 20000)
            ax2.tick_params(colors="#aaa", labelsize=6)
        p = os.path.join(OUT, "sfx_preview", f"{prefix}_{si // per + 1:02d}.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fig.savefig(p, facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(p)
    return paths


def run_sfx(only=None):
    outdir = os.path.join(OUT, "sfx_preview")
    os.makedirs(outdir, exist_ok=True)
    items, report = [], {}
    jobs = [(n, {}, n) for n in sfx.names()] + VARIANTS
    for name, kw, label in jobs:
        if only and not any(o in label for o in only):
            continue
        x = sfx.render(name, dur=kw.get("dur"), params=kw.get("params"), seed=kw.get("seed", 1))
        st = _stats(x)
        report[label] = st
        # previews are peak-safe: library-level sounds can exceed 0 dBFS in float
        y = x * min(1.0, 10 ** (-1.0 / 20) / max(1e-9, np.max(np.abs(x))))
        dsp.write_wav(os.path.join(outdir, f"{label}.wav"), y, bits=24)
        items.append((label, x, st))
    # signature determinism check
    a, b = sfx.render("match_strike", seed=1), sfx.render("match_strike", seed=999)
    sfx._CACHE.clear()
    c = sfx.render("match_strike", seed=5)
    report["_match_strike_identical"] = bool(np.array_equal(a, b) and np.array_equal(a, c))
    paths = sheets(items, "sheet")
    with open(os.path.join(outdir, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"{len(items)} previews -> {outdir}; match_strike identical: {report['_match_strike_identical']}")
    for p in paths:
        print(p)
    return paths


# ---------------------------------------------------------------------------- master checks
def check_master(x, sr=dsp.SR, expect_n=None):
    """Return a dict of objective checks on a finished master (float array (n, 2))."""
    res = {}
    res["samples"] = int(len(x))
    res["seconds"] = len(x) / sr
    if expect_n is not None:
        res["length_ok"] = int(len(x)) == int(expect_n)
    res["finite"] = bool(np.isfinite(x).all())
    res["dc_offset"] = [float(v) for v in np.mean(x, axis=0)]
    res["integrated_lufs"] = round(dsp.loudness_integrated(x, sr), 2)
    res["true_peak_dbtp"] = round(dsp.true_peak_db(x), 2)
    res["sample_peak_dbfs"] = round(dsp.sample_peak_db(x), 2)
    res["clicks"] = find_clicks(x, sr)
    return res


def find_clicks(x, sr=dsp.SR, thresh=8.0, max_report=20):
    """Sample-discontinuity detector: the 2nd difference of a 7 kHz-high-passed signal compared
    to its local (20 ms) RMS. A broadband step / spike stands out by > thresh x local level and
    above an absolute floor. Returns times (s) of the worst events."""
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


def overview(master, stems, scenes, path, events=None, title="Nobody Has a Face - loudness overview"):
    """Short-term (3 s) + momentary (0.4 s) loudness of the master, short-term of each stem,
    scene boundaries and labels, designed-silence / hit markers."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(22, 9), dpi=80, gridspec_kw=dict(height_ratios=[2.2, 1]))
    fig.patch.set_facecolor("#111")
    ax = axes[0]
    tm, lm = dsp.loudness_curve(master, win=0.4, hop=0.05)
    ts, ls = dsp.loudness_curve(master, win=3.0, hop=0.1)
    ax.plot(tm, lm, color="#666", lw=0.6, label="master momentary (0.4 s)")
    ax.plot(ts, ls, color="#f0b050", lw=1.6, label="master short-term (3 s)")
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
        for s in scenes:
            a.axvline(s["start"], color="#444", lw=0.8)
        a.set_facecolor("#000")
        a.tick_params(colors="#bbb")
        a.set_xlim(0, len(master) / dsp.SR)
        a.grid(color="#222")
    for s in scenes:
        ax.text(s["start"] + 0.2, -6, s["id"], color="#ddd", fontsize=9)
        ax.text(s["start"] + 0.2, -9, s["slug"][:11], color="#888", fontsize=7)
    for ev in events or []:
        ax.axvline(ev["t"], color=ev.get("color", "#c33"), lw=0.7, ls=":")
        ax.text(ev["t"], -60 + 2.5 * (hash(ev["label"]) % 4), ev["label"], color=ev.get("color", "#c33"), fontsize=7, rotation=90)
    ax.set_ylim(-62, -2)
    axes[1].set_ylim(-70, -5)
    ax.set_ylabel("LUFS", color="#bbb")
    axes[1].set_ylabel("stems LUFS (3 s)", color="#bbb")
    axes[1].set_xlabel("seconds", color="#bbb")
    ax.legend(loc="lower right", facecolor="#222", labelcolor="#ddd", fontsize=8)
    axes[1].legend(loc="lower right", facecolor="#222", labelcolor="#ddd", fontsize=8, ncol=4)
    ax.set_title(title, color="#eee")
    fig.tight_layout()
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def write_fake_vo(path, sr_out=44100):
    """Synthetic stand-in for the narration: a male formant 'voice' (no words) during every word
    span of timeline/vo_words.txt (source-take times). For pipeline QA only."""
    words = []
    with open(os.path.join(ROOT, "timeline", "vo_words.txt")) as fh:
        for ln in fh:
            if ln.startswith("#") or not ln.strip():
                continue
            w, a, b = ln.rstrip("\n").split("\t")
            words.append((float(a), float(b)))
    dur = 187.0
    sr = 16000
    n = int(dur * sr)
    rng = np.random.default_rng(55)
    v = sfx._formant_voice(n, rng, sr, f0=98.0, syl_rate=5.0, words=False)
    gate = np.zeros(n)
    for a, b in words:
        gate[int(a * sr):int(b * sr)] = 1.0
    gate = dsp.onepole_lp(gate, 30.0, sr)
    t = np.arange(n) / sr
    syl = 0.35 + 0.65 * np.sin(np.pi * 4.5 * t) ** 2
    x = v * gate * syl
    x = dsp.resample(x, sr, sr_out)
    x = 0.3 * x / (np.max(np.abs(x)) + 1e-9)
    dsp.write_wav(path, x, sr_out, bits=16)
    return path


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "sfx"
    if cmd == "sfx":
        run_sfx(argv[2:] or None)
    elif cmd == "zoom":
        # python3 -m audio.qa zoom NAME [t0 t1] [key=val ...]
        name = argv[2]
        rest = argv[3:]
        nums = [float(v) for v in rest if v.replace(".", "", 1).isdigit()][:2]
        params = dict(kv.split("=") for kv in rest if "=" in kv)
        params = {k: float(v) for k, v in params.items()}
        dur = params.pop("dur", None)
        x = sfx.render(name, dur=dur, params=params or None, seed=int(params.pop("seed", 1)) if "seed" in params else 1)
        if len(nums) == 2:
            x = x[dsp.n_of(nums[0]):dsp.n_of(nums[1])]
        p = sheets([(name + (" " + " ".join(rest) if rest else ""), x, _stats(x))], f"zoom_{name}", per=1, cols=1, scale=3.0)
        print(p[0])
    elif cmd == "fakevo":
        # python3 -m audio.qa fakevo OUT.wav : nonverbal formant babble on the source word times
        # (44.1 kHz mono 16-bit) - exercises the narration path of the mixer without the real take
        path = argv[2]
        write_fake_vo(path)
        print(path)
    elif cmd == "master":
        path = argv[2] if len(argv) > 2 else os.path.join(OUT, "audio_master.wav")
        x, sr = dsp.read_audio(path)
        from engine.timing import timeline
        n = int(round(timeline()["total_frames"] / timeline()["fps"] * sr))
        print(json.dumps(check_master(x, sr, n), indent=1))
    elif cmd == "overview":
        from engine.timing import timeline
        m, _ = dsp.read_audio(os.path.join(OUT, "audio_master.wav"))
        stems = {}
        for k in ("vo", "music", "sfx", "amb"):
            p = os.path.join(OUT, "stems", f"{k}.wav")
            stems[k] = dsp.read_audio(p)[0] if os.path.exists(p) else None
        print(overview(m, stems, timeline()["scenes"], os.path.join(OUT, "audio_overview.png")))
    else:
        print(__doc__)


if __name__ == "__main__":
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    main(sys.argv)
