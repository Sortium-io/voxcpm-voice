# voxcpm-voice

**In five minutes, you'll have a reusable cast of AI voices that sound exactly the same every time you use them.** Describe a drill sergeant, a villain, a hacker kid — or hand in an audio clip of a real voice you want to clone — and get a WAV in seconds. Pick what you love. Then have that voice say anything you want, any time you want. Your game, app, video, or podcast gets a voice cast you can call on forever.

You don't need voice actors. You don't need reference audio to start (though you can use one if you have one). You don't need to think about TTS models or diffusion parameters or prompt engineering. You just tell Claude what you want in plain English.

---

## What you can do with it

**Make a voice for your hero, villain, narrator, or announcer in under a minute.**
Ask Claude for "a gruff drill sergeant in his fifties". Get three takes to pick from. Done.

**Clone a real voice from an audio clip.**
Got a 15-second recording of a voice actor, your own voice, or any clean speech sample? Drop it in and Claude turns it into a voice in your library — same delivery every future line. Add a transcript for maximum fidelity.

**Keep the ones you like forever.**
Designed or imported, voices become permanent assets in your local library. Every future line sounds identical — no drift.

**Voice your entire script in the same voice later.**
Hand Claude a list of lines (or a YAML file) and it'll render the whole batch. Even 500 lines later, it's still the same character.

**Mix and match across scenes.**
A YAML file can render an entire multi-character scene — drill sergeant barks, hacker girl quips, announcer punctuates the moment — all in one pass.

**Steer delivery when you need a specific read.**
"Slower and more menacing." "Urgent, hushed." "Cheerful, faster." A `direction` on a line tells the model how to deliver it without changing who's speaking.

**Iterate without losing what works.**
"Re-roll the drill sergeant, deeper this time." Your saved reference is safe; only the rolls get replaced. When a better take arrives, swap it in. When it doesn't, nothing's lost.

---

## Install

```bash
claude plugin marketplace add Sortium-io/voxcpm-voice
claude plugin install voxcpm-voice
```

Restart your Claude Code session. That's it. First voice generation auto-installs the backing model (~2 GB, one-time). Every run after that is seconds.

### Prerequisites

- [Claude Code](https://claude.com/claude-code)
- macOS or Linux
- Python 3.10+
- ~3 GB free disk
- GPU helpful (Apple Silicon MPS / CUDA), not required

### Updating / uninstalling

```bash
claude plugin uninstall voxcpm-voice && claude plugin install voxcpm-voice   # updates
claude plugin marketplace remove voxcpm-voice                                  # forget the marketplace
rm -rf ~/voxcpm-voice                                                          # nuke the runtime (venv + voice library)
```

---

## Try it — design your first voice

Paste this into a Claude Code session:

```
Use the voxcpm-voice skill to audition a voice for me.
I want a gruff male drill sergeant in his fifties — weathered
gravelly baritone, shouted parade-ground commands, hoarse edge.
Give me 3 takes so I can pick the best one.
```

Claude generates three takes. Play them (on macOS: `open ~/voxcpm-voice/voices/Drill_Sergeant/samples/`). When one hits, say:

```
Save take 2 as the drill sergeant's reference.
```

## Now put the voice to work

You've got a saved drill sergeant. Use it:

```
Have the drill sergeant say: "Get your gear and move out, recruits!"
```

The output lands at `~/voxcpm-voice/voices/Drill_Sergeant/lines/`. Generate as many as you want — every line sounds like the same speaker.

For a full VO bank, hand Claude a batch:

```
Render these lines for the drill sergeant:
- "Fall in!"
- "Show me some hustle!"
- "On my mark!"
- "Water discipline. Check your canteens."
```

Or a YAML file if you're working from a script — template is at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml`. Copy it, fill in your lines, and tell Claude to render it. YAML also supports multi-voice scenes — different speakers in the same batch — and per-line `direction:` to steer delivery.

## Already have a voice you want to use?

If you've got a clean audio clip of a voice you want to clone — your own, a voice actor's, a sample recording — Claude can import it directly:

```
Import this audio as a new voice called Narrator_Sam:
  file: ~/Desktop/sam-intro.mp3
  transcript: "Hello, this is Sam reading a calibration paragraph."
```

The transcript is optional but worth including — with it, the skill uses VoxCPM's **Ultimate Cloning** to reproduce the voice with max fidelity. Without it, the skill uses **Controllable Cloning** — timbre locks, delivery is a bit more flexible.

Good reference clips:
- 10–25 seconds of clean speech
- Minimal background noise or music
- Delivery that matches how you'll want the voice used (calm clips make calm clones)

Once imported, the voice works exactly like a designed one — generate voicelines, batch via YAML, add direction per line.

## Steering delivery with `direction`

When you want a voice to say something a specific way — urgent, slower, angry, whispered — add a direction:

```
Have the drill sergeant say "fall back, regroup" — urgent, hushed.
```

The skill prepends a `(direction)` tag before the line. VoxCPM's Controllable Cloning keeps the voice's timbre locked while shifting delivery. Works for both designed and imported voices.

Use sparingly if you want pure reproduction of a cloned voice — direction shifts how it sounds. For "say exactly like the original", skip direction; for "say this line this way", include it.

### Prompts that work

- *"Make me a cyberpunk hacker girl — early twenties, sassy, mild Japanese accent."*
- *"I need a cold villain for a cartoon. Male, middle-aged, deliberate."*
- *"Import this clip as my voice — here's the transcript."*
- *"Narrate this paragraph in the grizzled detective voice."*
- *"Have Sam say 'we need to regroup' — urgent and low."*
- *"What voices have I saved?"*
- *"Re-roll the drill sergeant, deeper this time."*

If your description is thin, Claude asks 2–3 follow-ups (gender, age, accent, emotion). If it's concrete, it just runs.

---

## Tips that actually matter

**Concrete traits beat vibes.** *"Baritone around 100 Hz, gravelly, mid-forties, slight Boston accent"* gets you a specific voice. *"Cool deep voice"* gets you a generic one. Age, gender, timbre, accent, archetype — that's what the model weighs.

**Re-roll before you rewrite.** The model is stochastic — take 2 might be perfect without any prompt change. Ask for a re-roll before you edit the description.

**Once a voice is saved, never re-design it for new lines.** Ask for voicelines instead. Your saved voice stays locked; designing again would start over from scratch and drift.

**Exclamation marks do more than you think.** If a voice feels flat, punctuate the sentences more aggressively. `"Move out! Now!"` lands harder than `"Move out now."` — same meaning, different delivery.

---

## How it's organized on disk

Your voice library lives at `~/voxcpm-voice/voices/`:

```
~/voxcpm-voice/voices/<voice_name>/
├── voice.json        metadata, spoken transcript, imported flag, timestamps
├── reference.wav     the anchor for future lines
├── samples/          (designed voices only) rolls from each design session
└── lines/            every line the voice has ever spoken (kept forever)
    └── <batch>/      optional subfolder grouping for VO banks
```

**Designed** voices get their `reference.wav` from a saved sample (`save_take.py`). Re-designing overwrites `samples/` but leaves `reference.wav` and `lines/` intact.

**Imported** voices get their `reference.wav` directly from your audio file (`import_voice.py`). No `samples/` — the clip you provided is the anchor.

Once `reference.wav` is there, `speak.py` treats both the same way.

## Under the hood

The skill drives [VoxCPM2](https://github.com/OpenBMB/VoxCPM) in three modes, picked automatically based on what's in the library:

- **Voice Design** — text-only. You describe a voice; the model invents one. Used when designing from scratch.
- **Ultimate Cloning** — reference WAV + its transcript. Highest fidelity. Used for saved voices that have a transcript in `voice.json` (designed voices always do; imported voices have one if you gave one).
- **Controllable Cloning** — reference WAV only. Timbre locks, delivery flexible. Used for imported voices without transcripts, or when you pass `--direction` to steer delivery.

Defaults are the ones the VoxCPM paper evaluates on: `cfg_value=2.0`, `inference_timesteps=10`. A Chinese emotion directive is included by default on energetic voices because VoxCPM is bilingual and commits harder to Mandarin style tags than English equivalents (this is the kind of thing you only learn from a lot of experimentation; the skill just knows to do it).

---

## Direct CLI

The skill calls these behind the scenes, but they're scriptable if you want to bypass Claude.

**Design from text:**
```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/generate_voice.py" \
  --voice-name Drill_Sergeant \
  --voice-fantasy "gruff male drill sergeant in his fifties, gravelly baritone, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority" \
  --takes 3
```

**Import from audio:**
```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/import_voice.py" \
  --voice-name Narrator_Sam \
  --audio ~/Desktop/sam.mp3 \
  --text "Hello, this is Sam reading a calibration paragraph."
```
Omit `--text` for Controllable Cloning instead of Ultimate Cloning.

**Save a take (designed voices only):**
```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/save_take.py" \
  --name Drill_Sergeant --take 2
```

**Speak:**
```bash
# single line
.../speak.py --voice Drill_Sergeant --text "Get your gear and move out!"

# with direction (Controllable Cloning — shifts delivery)
.../speak.py --voice Narrator_Sam --text "..." --direction "slower, whispered, urgent"

# batch
.../speak.py --yaml path/to/voicelines.yaml
```

**List:**
```bash
.../list_voices.py
```

Full flag reference lives in [SKILL.md](skills/voxcpm-voice/SKILL.md).

---

## Troubleshooting

**First run looks stuck.** The model is downloading (~2 GB). Let it go.

**Voice sounds generic.** Description is too abstract. Add concrete traits (age, gender, timbre, accent). Re-roll.

**`speak.py` says "no reference.wav yet".** You haven't saved a take for that voice. Run save_take or tell Claude *"save take N"*.

**Sentences run together.** VoxCPM produced pauses shorter than 200 ms, so padding didn't fire. Add `[breath]` or `[quick_breath]` between sentences via `--lines`, or lower `--min-gap-ms` in the script.

**Torch/MPS errors on Apple Silicon.** The scripts set `PYTORCH_ENABLE_MPS_FALLBACK=1`. If something still fails, you can force CPU by editing `generate_voice.py` / `speak.py` to add `torch.set_default_device("cpu")` before the model load.

---

## Acknowledgements

- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB — the underlying TTS model.
- Harvard sentences for the default test set (standard TTS comparison corpus).
