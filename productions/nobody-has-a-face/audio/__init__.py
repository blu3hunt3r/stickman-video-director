"""Procedural sound for "Nobody Has a Face" (numpy/scipy only, 48 kHz stereo float32).

    audio.dsp        DSP primitives (oscillators, noise, filters, reverb, dynamics, metering, WAV I/O)
    audio.sfx        the SFX catalog: render(name, dur=None, params=None, seed=0) -> (n, 2)
    audio.ambience   continuous beds from the ambience map (production bible section 6)
    audio.score      the noir score (production bible section 7)
    audio.mix        python3 -m audio.mix [--vo PATH] [--no-vo]   -> out/audio_master.wav
    audio.qa         python3 -m audio.qa sfx|master|score          -> previews, contact sheets, checks
"""
