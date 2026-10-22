"""SALVAGE QA without ears.

    python3 films/salvage/audio/qa.py sfx [NAME ...]     # catalog (+ variants) -> out/sfx_preview/*.wav + sheet_*.png
    python3 films/salvage/audio/qa.py zoom NAME [t0 t1] [key=val ...]
    python3 films/salvage/audio/qa.py master [PATH]      # NaN/Inf, DC, clicks, length, LUFS, TP of the master
    python3 films/salvage/audio/qa.py overview           # out/audio_overview.png from the master + stems

Contact sheets: per sound a waveform (sample-peak lines) and a log-frequency spectrogram,
labelled with length, peak, true peak, DC and max momentary loudness.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio import dsp  # noqa: E402
from films.salvage.audio import sfx_salvage as S  # noqa: E402

OUT = os.path.join(ROOT, "films", "salvage", "out")
PREVIEW = os.path.join(OUT, "sfx_preview")

# variants rendered in addition to every catalog name at its defaults: (name, kwargs, label)
VARIANTS = [
    ("meridian_bell", dict(params=dict(strike=1.0, length=14.0)), "meridian_bell_full"),
    ("meridian_bell", dict(params=dict(strike=0.55, length=10.0, verb="dry")), "meridian_bell_dry_soft"),
    ("silt_puff", dict(params=dict(size=0.2)), "silt_puff_small"),
    ("silt_puff", dict(params=dict(size=1.0, metal=1.0)), "silt_puff_big_metal"),
    ("water_slap", dict(params=dict(size=1.0)), "water_slap_big"),
    ("pump_run", dict(dur=8.0, params=dict(spinup=0.0, rundown_at=3.0, rundown=3.0)), "pump_rundown"),
    ("winch_crank", dict(dur=6.0, params=dict(rate=0.8, load=0.9)), "winch_fast_heavy"),
    ("paper_slice", dict(params=dict(reverse=1)), "paper_slice_rev"),
    ("breath_single", dict(params=dict(phase="out", length=1.8)), "breath_single_out"),
    ("heartbeat_deep", dict(dur=8.0, params=dict(bpm=70, bpm_end=52)), "heartbeat_slowing"),
    ("uw_whoosh", dict(params=dict(size=1.0)), "uw_whoosh_big"),
    ("deck_step", dict(params=dict(weight=0.3)), "deck_step_light"),
]


def _stats(x):
    y = dsp.pad_to(x, max(len(x), dsp.n_of(0.4)))
    return dict(len_s=len(x) / dsp.SR, peak_db=dsp.sample_peak_db(x), tp_db=dsp.true_peak_db(x),
                dc=float(np.mean(x)), max_m=float(np.max(dsp.loudness_curve(y, win=0.4, hop=0.05)[1])),
                finite=bool(np.isfinite(x).all()))


def _spec(x, nfft=1024, hop=256):
    m = dsp.mono(x)
    if len(m) < nfft:
        m = np.pad(m, (0, nfft - len(m)))
    win = np.hanning(nfft)
    frames = 1 + (len(m) - nfft) // hop
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    Sx = np.abs(np.fft.rfft(m[idx] * win, axis=1)) + 1e-9
    Sx = 20 * np.log10(Sx / Sx.max())
    f = np.fft.rfftfreq(nfft, 1 / dsp.SR)
    t = (np.arange(frames) * hop + nfft / 2) / dsp.SR
    return t, f, Sx.T


def sheets(items, prefix, per=16, cols=4, scale=1.0, outdir=PREVIEW, nfft=1024):
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
            ts, fs, Sx = _spec(x, nfft=nfft, hop=nfft // 4)
            ax2.pcolormesh(ts, np.maximum(fs, 1.0), Sx, vmin=-90, vmax=0, cmap="magma", shading="auto")
            ax2.set_yscale("log")
            ax2.set_ylim(25, 20000)
            ax2.tick_params(colors="#aaa", labelsize=6)
        p = os.path.join(outdir, f"{prefix}_{si // per + 1:02d}.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        fig.savefig(p, facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(p)
    return paths


def run_sfx(only=None, write_wavs=True):
    os.makedirs(PREVIEW, exist_ok=True)
    items, report = [], {}
    jobs = [(n, {}, n) for n in S.names()] + VARIANTS
    for name, kw, label in jobs:
        if only and not any(o in label for o in only):
            continue
        x = S.render(name, dur=kw.get("dur"), params=kw.get("params"), seed=kw.get("seed", 1))
        st = _stats(x)
        st["anchor"] = S.anchor(name, kw.get("params"))
        report[label] = st
        if write_wavs:
            y = x * min(1.0, 10 ** (-1.0 / 20) / max(1e-9, float(np.max(np.abs(x)))))
            dsp.write_wav(os.path.join(PREVIEW, f"{label}.wav"), y, bits=24)
        items.append((label, x, st))
    # determinism: same seed, same take; another seed, another take
    S._CACHE.clear()
    a = S.render("tumbler_click", seed=3)
    S._CACHE.clear()
    b = S.render("tumbler_click", seed=3)
    c = S.render("tumbler_click", seed=4)
    report["_deterministic"] = bool(np.array_equal(a, b))
    report["_seed_varies"] = not bool(np.array_equal(a, c))
    paths = sheets(items, "sheet" if not only else "sel")
    with open(os.path.join(PREVIEW, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    bad = [k for k, v in report.items() if isinstance(v, dict) and (not v["finite"] or abs(v["dc"]) > 1e-3)]
    print(f"{len(items)} previews -> {PREVIEW}; deterministic {report['_deterministic']}, seed varies "
          f"{report['_seed_varies']}; problems: {bad or 'none'}")
    for p in paths:
        print(p)
    return paths


# ---------------------------------------------------------------------------- master checks
def find_clicks(x, sr=dsp.SR, thresh=8.0, max_report=20):
    """Sample-discontinuity detector: the 2nd difference of a 7 kHz-high-passed signal against
    its local (20 ms) RMS. Returns times (s) of the worst events."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    hp = dsp.sos(x, "highpass", 7000.0, 4)
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


def overview(master, stems, scenes, path, events=None, silences=(), title="SALVAGE - loudness overview"):
    """Short-term (3 s) and momentary (0.4 s) loudness of the master with scene boundaries,
    designed hits (markers) and designed silences (shaded); stems' short-term loudness below."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(24, 10), dpi=80, gridspec_kw=dict(height_ratios=[2.3, 1]))
    fig.patch.set_facecolor("#111")
    ax = axes[0]
    tm, lm = dsp.loudness_curve(master, win=0.4, hop=0.05)
    ts, ls = dsp.loudness_curve(master, win=3.0, hop=0.1)
    ax.plot(tm, lm, color="#666", lw=0.6, label="master momentary (0.4 s)")
    ax.plot(ts, ls, color="#f0b050", lw=1.7, label="master short-term (3 s)")
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
        for a0, a1 in silences:
            a.axvspan(a0, a1, color="#203040", alpha=0.6)
        a.set_facecolor("#000")
        a.tick_params(colors="#bbb")
        a.set_xlim(0, len(master) / dsp.SR)
        a.grid(color="#222")
    for s in scenes:
        ax.text(s["start"] + 0.2, -5, s["id"], color="#ddd", fontsize=9)
        ax.text(s["start"] + 0.2, -8, s["slug"][:11], color="#888", fontsize=7)
    for k, ev in enumerate(events or []):
        ax.axvline(ev["t"], color=ev.get("color", "#c33"), lw=0.7, ls=":")
        ax.text(ev["t"], -61 + 3.0 * (k % 5), ev["label"], color=ev.get("color", "#c33"), fontsize=7, rotation=90)
    ax.set_ylim(-64, -2)
    axes[1].set_ylim(-72, -5)
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


def zoom(name, rest):
    nums = []
    for v in rest:
        try:
            nums.append(float(v))
        except ValueError:
            pass
    params = {}
    for kv in rest:
        if "=" in kv:
            k, v = kv.split("=", 1)
            try:
                params[k] = float(v)
            except ValueError:
                params[k] = v
    dur = params.pop("dur", None)
    seed = int(params.pop("seed", 1))
    x = S.render(name, dur=dur, params=params or None, seed=seed)
    if len(nums) >= 2:
        x = x[dsp.n_of(nums[0]):dsp.n_of(nums[1])]
    label = name + (" " + " ".join(rest) if rest else "")
    p = sheets([(label, x, _stats(x))], f"zoom_{name}", per=1, cols=1, scale=3.0, nfft=2048)
    dsp.write_wav(os.path.join(PREVIEW, f"zoom_{name}.wav"), x * min(1.0, 0.89 / max(1e-9, float(np.max(np.abs(x))))), bits=24)
    return p[0]


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "sfx"
    if cmd == "sfx":
        run_sfx(argv[2:] or None)
    elif cmd == "zoom":
        print(zoom(argv[2], argv[3:]))
    elif cmd == "master":
        path = argv[2] if len(argv) > 2 else os.path.join(OUT, "audio_master.wav")
        x, sr = dsp.read_audio(path)
        from engine.timing import timeline
        tl = timeline("salvage")
        n = int(round(tl["frames"] / tl["fps"] * sr))
        print(json.dumps(check_master(x, sr, n), indent=1))
    elif cmd == "overview":
        from engine.timing import timeline
        m, _ = dsp.read_audio(os.path.join(OUT, "audio_master.wav"))
        stems = {}
        for k in ("vo", "music", "sfx", "amb"):
            p = os.path.join(OUT, "stems", f"{k}.wav")
            stems[k] = dsp.read_audio(p)[0] if os.path.exists(p) else None
        print(overview(m, stems, timeline("salvage")["scenes"], os.path.join(OUT, "audio_overview.png")))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
