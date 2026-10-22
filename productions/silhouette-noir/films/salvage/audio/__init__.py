"""SALVAGE soundtrack (48 kHz, numpy/scipy, fully procedural except the narration take).

    sfx_salvage  - this film's sound catalog (diver, boat, wreck, the cut, the dial, the bell)
    cuesheet     - the designed cue sheet from the bible's beat timings + scene-cue merging
    ambience     - beds: dusk surface, underwater pressure by depth, wreck interior, night deck
    score        - the D-minor score (drones, Bass/Bernstein ostinato, heartbeat, the bell's key)
    mix          - re-recording mix -> films/salvage/out/audio_master.wav (+ stems, report, plot)
    qa           - SFX preview sheets and master checks

Run from the production root:  python3 films/salvage/audio/mix.py [--no-vo]
"""
