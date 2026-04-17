# voxcpm-voice

**In five minutes, you'll have a reusable cast of AI voices that sound exactly the same every time you use them.** Describe a drill sergeant, a villain, a hacker kid — whatever your project needs — and get a WAV in seconds. Pick the take you love. Then have that voice say anything you want, any time you want. Your game, app, video, or podcast gets a voice cast you can call on forever, without ever recording a single line.

You don't need voice actors. You don't need reference audio to start. You don't need to think about TTS models or diffusion parameters or prompt engineering. You just tell Claude what you want in plain English.

---

## What you can do with it

**Make a voice for your hero, villain, narrator, or announcer in under a minute.**
Ask Claude for "a gruff drill sergeant in his fifties". Get three takes to pick from. Done.

**Keep the ones you like forever.**
Say "save take 2" and that voice becomes a permanent asset in your local library. Every future line you generate in that voice will sound identical — no drift.

**Voice your entire script in that voice later.**
Hand Claude a list of lines (or a YAML file) and it'll render the whole batch. Cloning mode locks every line to your saved reference, so even 500 lines later it's still the same character.

**Mix and match across scenes.**
A YAML file can render an entire multi-character scene — drill sergeant barks, hacker girl quips, announcer punctuates the moment — all in one pass.

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

Or a YAML file if you're working from a script — template is at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml`. Copy it, fill in your lines, and tell Claude to render it. YAML also supports multi-voice scenes — different speakers in the same batch.

### Prompts that work

- *"Make me a cyberpunk hacker girl — early twenties, sassy, mild Japanese accent."*
- *"I need a cold villain for a cartoon. Male, middle-aged, deliberate."*
- *"Narrate this paragraph in the grizzled detective voice."*
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
├── voice.json        the voice's metadata and prompt
├── reference.wav     your saved take — the anchor for future lines
├── samples/          rolls from each design session (overwritten on re-roll)
└── lines/            everything the voice has ever said (kept forever)
    └── <batch>/      optional subfolder grouping for VO banks
```

When you re-design a voice, only `samples/` is overwritten. Your saved `reference.wav` and every line you've ever generated are safe.

## Under the hood

The skill drives [VoxCPM2](https://github.com/OpenBMB/VoxCPM) in two modes. Design mode is text-only — you describe a voice and the model invents one. Cloning mode takes your saved reference WAV plus its transcript (we keep both) and locks future generations to that exact voice.

Defaults are the ones the VoxCPM paper evaluates on: `cfg_value=2.0`, `inference_timesteps=10`. A Chinese emotion directive is included by default on energetic voices because VoxCPM is bilingual and commits harder to Mandarin style tags than English equivalents (this is the kind of thing you only learn from a lot of experimentation; the skill just knows to do it).

---

## Direct CLI

The skill calls these behind the scenes, but they're scriptable if you want to bypass Claude.

**Design:**
```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/generate_voice.py" \
  --voice-name Drill_Sergeant \
  --voice-fantasy "gruff male drill sergeant in his fifties, gravelly baritone, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority" \
  --takes 3
```

**Save a take:**
```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/save_take.py" \
  --name Drill_Sergeant --take 2
```

**Speak:**
```bash
# single line
.../speak.py --voice Drill_Sergeant --text "Get your gear and move out!"

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
