"""SHADOW PLAY - QA without ears.

    python3 films/shadowplay/audio/qa.py sfx [NAME ...]   # this film's SFX (+ variants) ->
                                                          #   films/shadowplay/out/sfx_preview/*.wav + sheet_*.png
    python3 films/shadowplay/audio/qa.py zoom NAME [t0 t1] [key=val ...]   # one sound, big
    python3 films/shadowplay/audio/qa.py master [PATH]    # NaN/Inf, DC, clicks, length, LUFS, TP
    python3 films/shadowplay/audio/qa.py overview         # out/audio_overview.png from the written master

Contact sheets show, per sound: waveform (sample-peak lines) and a log-frequency spectrogram,
labelled with length, peak, true peak, DC and max momentary loudness.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from audio import dsp  # noqa: E402
from films.shadowplay.audio import sfx_shadowplay as S  # noqa: E402

FILM = "shadowplay"
OUT = os.path.join(ROOT, "films", FILM, "out")
PREVIEW = os.path.join(OUT, "sfx_preview")

# variants rendered in addition to every own sound at its defaults: (name, kwargs, label)
VARIANTS = [
    ("switch_click", dict(params=dict(dist=1.0)), "switch_click_across_street"),
    ("switch_click", dict(params=dict(off=1)), "switch_click_off"),
    ("bulb_on", dict(params=dict(dist=0.55)), "bulb_on_dist0.55"),
    ("light_out", dict(params=dict(dist=0.55)), "light_out_dist0.55"),
    ("binocular_lift", dict(params=dict(lower=1)), "binocular_lower"),
    ("sheet_rip", dict(params=dict(size=0.15)), "sheet_rip_s0.15"),
    ("sheet_rip", dict(params=dict(size=1.0), seed=2), "sheet_rip_s1_seed2"),
    ("sheet_rip", dict(params=dict(size=0.6), seed=3), "sheet_rip_s0.6_seed3"),
    ("string_stab", dict(params=dict(step=1, size=0.6)), "string_stab_step1"),
    ("string_stab", dict(params=dict(step=2, size=0.8)), "string_stab_step2"),
    ("string_stab", dict(params=dict(step=3, size=1.0)), "string_stab_step3"),
    ("stair_steps", dict(dur=2.2, params=dict(who="her", rate=4.6, d0=0.1, d1=0.85, spin=0.6)), "stair_her_down_away"),
    ("stair_steps", dict(dur=3.3, params=dict(who="him", rate=1.8, d0=0.95, d1=0.15, spin=0.25, creak=0.6)), "stair_him_approach"),
    ("steps_seq", dict(dur=1.4, params=dict(kind="wet", rate=2.6, weight=0.5)), "steps_wet"),
    ("steps_seq", dict(dur=1.4, params=dict(kind="floor", who="him", rate=1.8, weight=0.9)), "steps_floor_him"),
    ("wood_step", dict(params=dict(who="him", weight=0.9, creak=1.0, stair=1)), "wood_step_him_creak"),
    ("siren_wail", dict(dur=4.0, params=dict(mode="winddown", cars=1)), "siren_winddown"),
    ("siren_wail", dict(dur=4.0, params=dict(mode="far", cars=2)), "siren_far"),
    ("siren_whoop", dict(params=dict(dist=0.0)), "siren_whoop_close"),
    ("police_radio", dict(params=dict(dist=0.8)), "police_radio_far"),
    ("curtain_rings", dict(params=dict(part=1)), "curtain_part"),
    ("breath", dict(params=dict(kind="in")), "breath_in"),
    ("iris_close", dict(params=dict(rect=1)), "iris_rect"),
    ("door_hammer", dict(dur=3.0), "door_hammer_3s"),
    ("handle_turn", dict(params=dict(length=1.3), seed=4), "handle_turn_1.3_seed4"),
    ("window_lights", dict(params=dict(off=1, n=9, span=1.8)), "window_lights_off"),
    ("window_lights", dict(params=dict(times=(0.0, 0.075, 0.225, 0.3, 0.31, 0.375, 0.45, 0.525, 0.6),
                                       pans=(0.23, -0.23, -0.23, 0.23, 0.46, -0.46, -0.23, 0.0, -0.23))), "window_lights_s01"),
    ("paper_slide", dict(params=dict(length=0.2, tap=0, shape="out", pan0=-0.85, pan1=0.85)), "paper_slide_whisk"),
    ("paper_slide", dict(params=dict(length=0.24, tap=0, shape="in", pan0=0.95, pan1=0.23)), "paper_slide_card"),
]


def _stats(x):
    m = dsp.loudness_curve(dsp.pad_to(x, max(len(x), dsp.n_of(0.4))), win=0.4, hop=0.05)[1]
    return dict(len_s=len(x) / dsp.SR, peak_db=dsp.sample_peak_db(x), tp_db=dsp.true_peak_db(x),
                dc=float(np.mean(x)), max_m=float(np.max(m)) if len(m) else -70.0,
                finite=bool(np.isfinite(x).all()))


def _spec(x, nfft=1024, hop=256):
    m = dsp.mono(x)
    if len(m) < nfft:
        m = np.pad(m, (0, nfft - len(m)))
    win = np.hanning(nfft)
    frames = 1 + (len(m) - nfft) // hop
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    spec = np.abs(np.fft.rfft(m[idx] * win, axis=1)) + 1e-9
    spec = 20 * np.log10(spec / spec.max())
    f = np.fft.rfftfreq(nfft, 1 / dsp.SR)
    t = (np.arange(frames) * hop + nfft / 2) / dsp.SR
    return t, f, spec.T


def sheets(items, prefix, per=16, cols=4, scale=1.0, outdir=PREVIEW):
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
            ts, fs, spec = _spec(x)
            ax2.pcolormesh(ts, np.maximum(fs, 1.0), spec, vmin=-90, vmax=0, cmap="magma", shading="auto")
            ax2.set_yscale("log")
            ax2.set_ylim(25, 20000)
            ax2.tick_params(colors="#aaa", labelsize=6)
        p = os.path.join(outdir, f"{prefix}_{si // per + 1:02d}.png")
        os.makedirs(outdir, exist_ok=True)
        fig.savefig(p, facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(p)
    return paths


def run_sfx(only=None):
    os.makedirs(PREVIEW, exist_ok=True)
    items, report = [], {}
    jobs = [(n, {}, n) for n in S.names()] + VARIANTS
    for name, kw, label in jobs:
        if only and not any(o in label for o in only):
            continue
        x = S.render(name, dur=kw.get("dur"), params=kw.get("params"), seed=kw.get("seed", 1))
        st = _stats(x)
        report[label] = st
        y = x * min(1.0, 10 ** (-1.0 / 20) / max(1e-9, float(np.max(np.abs(x)))))
        dsp.write_wav(os.path.join(PREVIEW, f"{label}.wav"), y, bits=24)
        items.append((label, x, st))
    # determinism: the same seed renders bit-identical takes after a cache flush
    a = S.render("sheet_rip", params=dict(size=0.6), seed=7)
    S._CACHE.clear()
    b = S.render("sheet_rip", params=dict(size=0.6), seed=7)
    c = S.render("sheet_rip", params=dict(size=0.6), seed=8)
    report["_deterministic"] = bool(np.array_equal(a, b))
    report["_seed_varies"] = bool(not np.array_equal(a[:min(len(a), len(c))], c[:min(len(a), len(c))]))
    paths = sheets(items, "sheet" if not only else "sheet_sel")
    with open(os.path.join(PREVIEW, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"{len(items)} previews -> {PREVIEW}; deterministic {report['_deterministic']}, "
          f"seed varies {report['_seed_varies']}")
    for p in paths:
        print(p)
    return paths


# ---------------------------------------------------------------------------- master checks
def find_clicks(x, sr=dsp.SR, thresh=8.0, max_report=20, return_count=False):
    """Sample-discontinuity detector: the 2nd difference of a 7 kHz-high-passed signal against
    its local (20 ms) RMS. Returns the worst events as {t, score, level_db}."""
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
    total = len(events)
    events = sorted(events, key=lambda k: -score[k])[:max_report]
    if return_count:
        return [dict(t=round((k + 1) / sr, 4), score=round(float(score[k]), 1), level_db=round(float(dsp.lin2db(d2[k])), 1))
                for k in sorted(events)], total
    return [dict(t=round((k + 1) / sr, 4), score=round(float(score[k]), 1), level_db=round(float(dsp.lin2db(d2[k])), 1))
            for k in sorted(events)]


def check_master(x, sr=dsp.SR, expect_n=None):
    res = dict(samples=int(len(x)), seconds=len(x) / sr)
    if expect_n is not None:
        res["length_ok"] = int(len(x)) == int(expect_n)
    res["finite"] = bool(np.isfinite(x).all())
    res["dc_offset"] = [float(v) for v in np.mean(x, axis=0)]
    res["integrated_lufs"] = round(dsp.loudness_integrated(x, sr), 2)
    res["true_peak_dbtp"] = round(dsp.true_peak_db(x), 2)
    res["sample_peak_dbfs"] = round(dsp.sample_peak_db(x), 2)
    res["clicks"], res["click_candidates_total"] = find_clicks(x, sr, return_count=True)
    return res


def overview(master, stems, scenes, path, events=None, title="SHADOW PLAY - loudness overview", arc=None):
    """Momentary (0.4 s) + short-term (3 s) loudness of the master, short-term of each stem,
    scene boundaries / slugs, hit markers (events: [{t, label, color}]); arc: optional
    [(t0, t1, lufs)] target segments drawn as grey bars."""
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
    for t0, t1, v in arc or []:
        ax.plot([t0, t1], [v, v], color="#8a8a8a", lw=3, alpha=0.5)
    colors = dict(vo="#ffffff", music="#5090ff", sfx="#e04050", amb="#40c080")
    for k, x in stems.items():
        if x is None or not np.any(x):
            continue
        t2, l2 = dsp.loudness_curve(x, win=3.0, hop=0.1)
        axes[1].plot(t2, l2, lw=1.0, color=colors.get(k, "#ccc"), label=f"{k} short-term")
    integ = dsp.loudness_integrated(master)
    ax.axhline(integ, color="#f0b050", lw=0.6, ls="--")
    ax.text(1, integ + 0.6, f"integrated {integ:.1f} LUFS  TP {dsp.true_peak_db(master):.1f} dBTP", color="#f0b050", fontsize=9)
    for a in axes:
        for s in scenes:
            a.axvline(s["start"], color="#444", lw=0.8)
        a.set_facecolor("#000")
        a.tick_params(colors="#bbb")
        a.set_xlim(0, len(master) / dsp.SR)
        a.grid(color="#222")
    for s in scenes:
        ax.text(s["start"] + 0.2, -6, s["id"], color="#ddd", fontsize=9)
        ax.text(s["start"] + 0.2, -9, s.get("slug", "")[:12], color="#888", fontsize=7)
    for k, ev in enumerate(events or []):
        ax.axvline(ev["t"], color=ev.get("color", "#c33"), lw=0.7, ls=":")
        ax.text(ev["t"], -60 + 2.6 * (k % 5), ev["label"], color=ev.get("color", "#c33"), fontsize=7, rotation=90)
    ax.set_ylim(-62, -2)
    axes[1].set_ylim(-70, -5)
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


def zoom(name, rest):
    nums = [float(v) for v in rest if v.replace(".", "", 1).isdigit()][:2]
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
    if len(nums) == 2:
        x = x[dsp.n_of(nums[0]):dsp.n_of(nums[1])]
    p = sheets([(name + (" " + " ".join(rest) if rest else ""), x, _stats(x))], f"zoom_{name}", per=1, cols=1, scale=3.0)
    return p[0]


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "sfx"
    if cmd == "sfx":
        run_sfx(argv[2:] or None)
    elif cmd == "zoom":
        print(zoom(argv[2], argv[3:]))
    elif cmd == "master":
        from engine.timing import timeline
        path = argv[2] if len(argv) > 2 else os.path.join(OUT, "audio_master.wav")
        x, sr = dsp.read_audio(path)
        tl = timeline(FILM)
        print(json.dumps(check_master(x, sr, int(round(tl["duration"] * sr))), indent=1))
    elif cmd == "overview":
        from engine.timing import timeline
        tl = timeline(FILM)
        m, _ = dsp.read_audio(os.path.join(OUT, "audio_master.wav"))
        stems = {}
        for k in ("vo", "music", "sfx", "amb"):
            p = os.path.join(OUT, "stems", f"{k}.wav")
            stems[k] = dsp.read_audio(p)[0] if os.path.exists(p) else None
        print(overview(m, stems, tl["scenes"], os.path.join(OUT, "audio_overview.png")))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
