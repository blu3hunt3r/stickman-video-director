"""RED: the film's procedural soundtrack (48 kHz, numpy/scipy only).

    common.py    film clock, word anchors, acoustic spaces (synthesized IRs), render cache
    sfx_red.py   this film's SFX catalog (snow, wolf, spider, basket, fire, village, Bass graphics)
    cuesheet.py  the designed cue sheet (from the bible's beats) + merging of scene cues(T) hints
    ambience.py  continuous beds per scene, crossfaded across cuts; THE SILENCE (s03 'quieter')
    score.py     the score: the A-minor lullaby (music box, solo violin, orchestra), choir, chase
    mix.py       the re-recording mix -> films/red/out/audio_master.wav (+ stems, report, plot)
    qa.py        QA without ears: SFX previews + contact sheets, master checks, overview plot

Run everything from the production root:  python3 films/red/audio/mix.py [--no-vo]
"""
