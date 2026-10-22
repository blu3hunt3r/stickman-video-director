"""Shared procedural-audio library for the trilogy (48 kHz, numpy/scipy).

    audio.dsp  - DSP primitives: oscillators, noise, envelopes, filters, physical models,
                 synthesized reverbs, dynamics, BS.1770 loudness / true-peak metering, WAV io
    audio.sfx  - the SFX catalog: sfx.render(name, dur, params, seed) -> (n, 2) float32

audio/reference/ holds the previous film's score, ambience, mix and QA modules as worked
examples (not importable as-is). Each film's sound lives in films/<film>/audio/.
"""
