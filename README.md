# voxcpm-voice

A Claude Code skill that designs, saves, and reuses voices using [VoxCPM2](https://github.com/OpenBMB/VoxCPM). Describe a voice in plain English, pick your favorite take, then generate any new voicelines or narration in that voice — it'll sound the same every time.

No reference audio needed to *create* a voice. Once you save one, it becomes a reusable asset in a local library.

## What it does

Three phases, picked automatically based on what you ask Claude:

1. **Design a voice** — describe what you want (*"a gruff drill sergeant"*), and the skill expands that into VoxCPM's stacked-directive format and generates N takes. Voice-design mode: text-only, no reference audio required.
2. **Save a take** — once you hear a take you like, tell Claude *"keep take 2"* and the skill promotes it to the voice's `reference.wav`. That voice is now a reusable asset in your library.
3. **Speak in a saved voice** — later, *"have the drill sergeant say 'get your gear and move out'"* or *"render these 20 training lines for the drill sergeant"* and the skill uses VoxCPM's **Ultimate Cloning** (reference audio + transcript) to generate new lines that sound *exactly* like your saved voice. No drift across renders.

Supports YAML batches for full VO banks (one voice, many lines) and multi-voice scenes.

The defaults codify what's been validated empirically:

- `cfg_value=2.0`, `inference_timesteps=10` — VoxCPM's README-evaluated config.
- Chinese emotion directive on by default — VoxCPM2 is bilingual and commits harder to Mandarin directives than English equivalents.
- Single-generate-per-take for voice consistency within a design.
- Ultimate Cloning (reference + transcript) for consistency across generations.

## Library layout

The skill maintains a local library at `~/voxcpm-voice/voices/`:

```
~/voxcpm-voice/voices/<voice_name>/
├── voice.json            metadata (prompt, spoken sentences, reference_take, timestamps)
├── reference.wav         the chosen take — anchor for future voicelines
├── samples/              design rolls (overwritten when re-designing this voice)
│   ├── t1.wav
│   └── t2.wav
└── lines/                cloned voicelines from speak (accumulates; never blown away)
    ├── get_your_gear_and_move_out.wav
    └── training-vo/
        ├── fall_in.wav
        └── on_my_mark.wav
```

Re-designing a voice overwrites `samples/` but leaves `reference.wav` and `lines/` alone — so you can iterate on a design without losing a good reference you already saved.

## Prerequisites

- [Claude Code](https://claude.com/claude-code) (this is a Claude Code skill)
- macOS or Linux (tested on macOS; Linux should work)
- Python 3.10 or newer with `venv` module
- ~3 GB free disk for the Python venv + VoxCPM2 model weights
- GPU helpful but not required (Apple Silicon MPS, CUDA, or CPU)

## Install

```bash
claude plugin marketplace add Sortium-io/voxcpm-voice
claude plugin install voxcpm-voice
```

That's it. Next time you start a Claude Code session, the skill is available. Ask for a voice in plain English and Claude will take it from there.

First voice generation triggers an auto-setup:

- Creates a Python venv at `~/voxcpm-voice/voxcpm-venv/`
- Installs `voxcpm`, `soundfile`, `torchaudio`, `numpy`, `pyyaml`
- Downloads the VoxCPM2 model weights (~2 GB) from HuggingFace

Subsequent runs skip all of that — setup is idempotent, weights are cached.

### Updating

```bash
claude plugin update voxcpm-voice
```

### Uninstalling

```bash
claude plugin uninstall voxcpm-voice
claude plugin marketplace remove voxcpm-voice   # optional: also forget the marketplace
rm -rf ~/voxcpm-voice                           # optional: nuke the runtime (venv + voice library)
```

## Usage

Once the plugin's installed, start a Claude Code session and describe the voice you want in plain English. The skill walks you through the three phases (design → save → speak) conversationally. On first use it'll spend ~2 min building the Python venv and ~1 min downloading the VoxCPM2 model (one-time). Afterwards, design takes ~10 s per take; voicelines take 1–5 s each.

### Kick it off — design your first voice

Paste this into Claude Code to try it:

```
Use the voxcpm-voice skill to audition a voice for me.
I want a gruff male drill sergeant in his fifties — weathered
gravelly baritone, shouted parade-ground commands, hoarse edge.
Give me 3 takes so I can pick the best one.
```

Claude generates 3 takes into `~/voxcpm-voice/voices/Drill_Sergeant/samples/`. Play them (on macOS: `open ~/voxcpm-voice/voices/Drill_Sergeant/samples/`). When one nails it, tell Claude:

```
Save take 2 as the drill sergeant's reference.
```

That promotes `samples/t2.wav` to `reference.wav`. The voice is now a reusable asset.

### Use the saved voice

```
Have the drill sergeant say: "Get your gear and move out, recruits!"
```

Claude runs Ultimate Cloning using the saved reference. Output lands at `~/voxcpm-voice/voices/Drill_Sergeant/lines/get_your_gear_and_move_out_recruits.wav`. Every line you generate sounds identical to your saved voice — no drift.

### Batch VO (many lines, one voice)

For a full VO bank, use the YAML template at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml`. Copy it, edit, and tell Claude:

```
Render all the lines in ~/my-training-vo.yaml
```

One model load, all lines rendered. Supports multi-voice scenes too — per-line `voice:` override lets you mix speakers in one YAML file.

### More prompts that trigger the skill

- *"Make me a voice that sounds like a cyberpunk hacker girl — early twenties, sassy, mild Japanese accent."*
- *"I need a cold villain voice for a cartoon. Male, middle-aged, deliberate."*
- *"Narrate this paragraph in the grizzled detective voice."* (requires a saved voice named `grizzled_detective` or similar)
- *"What voices have I saved?"* → lists the library.
- *"Re-roll the drill sergeant, deeper this time."* → re-designs under the same name; `reference.wav` stays intact.

If your description is thin, Claude will ask 2–3 targeted follow-ups (gender, age, accent, emotion, context) before generating. If it's concrete enough, it generates immediately.

### Direct CLI usage

The skill calls these under the hood; you can invoke them directly once the plugin is installed. `${CLAUDE_PLUGIN_ROOT}` resolves to the plugin install path.

**Design a new voice** (`generate_voice.py`):

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/generate_voice.py" \
  --voice-name "Drill_Sergeant" \
  --voice-fantasy "gruff male drill sergeant in his fifties, weathered gravelly baritone, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority, hard clipped cadence, explosive bark" \
  --takes 3
```

Writes `~/voxcpm-voice/voices/Drill_Sergeant/samples/t1.wav`, `t2.wav`, `t3.wav` + `voice.json`.

Flags: `--voice-name` (required), `--voice-fantasy`, `--emotion`, `--no-chinese-hype`, `--takes N`, `--lines "..." "..." "..."`, `--cfg-value`, `--inference-timesteps`, `--save-take N` (promote a take immediately), `--output-dir PATH` (bypass the library), `--skip-padding`, `--dry-run`.

**Promote a take** (`save_take.py`):

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/save_take.py" \
  --name Drill_Sergeant --take 2
```

Copies `samples/t2.wav` → `reference.wav`; updates `voice.json`.

**Speak in a saved voice** (`speak.py`):

```bash
# Single line
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --voice Drill_Sergeant --text "Get your gear and move out!"

# Multiple lines, same voice
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --voice Drill_Sergeant --lines "Fall in!" "On my mark!" "At ease."

# Full YAML batch (single or multi-voice)
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --yaml path/to/voicelines.yaml
```

Template at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml`. Flags: `--voice`, `--text`, `--lines`, `--yaml`, `--batch` (subfolder under `lines/`), `--takes N`, `--cfg-value`, `--inference-timesteps`, `--skip-padding`, `--dry-run`.

**List the library** (`list_voices.py`):

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/list_voices.py"
```

## How it works

VoxCPM2 reads `()`-wrapped prefixes as **voice conditioning**, not as speech. So the text passed to the model looks like:

```
(concrete voice description)(emotion/style directive)(Chinese hype directive)Sentence one! Sentence two! Sentence three!
```

Everything before the last `)` is style spec; only what follows is spoken. Three things matter:

**Concrete traits beat subjective ones.** *"Baritone around 100 Hz, gravelly, mid-forties"* gives the model more to lock onto than *"cool deep voice"*. Age, gender, timbre, accent, archetype — these are what VoxCPM weighs.

**Chinese directives commit harder than English.** Counterintuitive but reliable: `请用极度激动和兴奋的语气大声喊` produces more actual shouting than the English equivalent. VoxCPM2 is bilingual and weights Mandarin descriptors more strongly.

**Emotion lives in the directive, not in `cfg_value`.** If the output feels flat, strengthen the emotion phrase, add exclamation marks on the sentences, or drop in `[breath]` / `[quick_breath]` tags between sentences — don't reach for higher cfg. Pushing cfg can cause digital/compressed artifacts instead of more commitment.

## Prompt examples that work

| User asks for | Voice fantasy | Emotion |
|---|---|---|
| Arena PA | `deep gravelly male arena announcer, forties, PA-system reverb` | `SHOUTING with explosive adrenaline hype, urgent commanding bark` |
| Drill sergeant | `gruff male drill sergeant in his fifties, weathered gravelly baritone, hoarse edge` | `SHOUTING with parade-ground authority, hard clipped cadence` |
| Cyberpunk hacker girl | `playful young female cyberpunk hacker in her early twenties, wry sassy tone, light Japanese-accented English, gamer energy` | `cocky playful hype, smirking delivery` |
| Movie trailer | `booming male cinematic trailer announcer, rich low chest voice, epic theatrical gravitas, slow deliberate pacing` | `epic trailer intensity, grand declarations` |
| Cold villain | `cold male villain in his fifties, quiet measured baritone, clipped precise diction, detached menace` | _(leave empty — quiet villains lose menace if you add shout)_ — also `--no-chinese-hype` |
| AI assistant | `neutral synthetic female assistant AI, clean even timbre, friendly professional` | _(leave empty)_ — also `--no-chinese-hype` |

## Repo layout

```
voxcpm-voice/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── skills/voxcpm-voice/
│   ├── SKILL.md                      # The Claude Code skill definition
│   ├── scripts/
│   │   ├── setup.sh                  # Idempotent venv installer
│   │   ├── generate_voice.py         # Design a new voice (voice-design mode)
│   │   ├── save_take.py              # Promote a sample to reference.wav
│   │   ├── speak.py                  # Speak in a saved voice (Ultimate Cloning)
│   │   ├── list_voices.py            # List the library
│   │   ├── _library.py               # Shared library helpers
│   │   └── _silence.py               # Silence-pad post-processing
│   └── templates/
│       └── voicelines.yaml           # Copy this for batch speak runs
└── README.md
```

After `setup.sh` runs, the following is created in your home directory:

```
~/voxcpm-voice/
├── voxcpm-venv/              # Python venv with voxcpm + deps
└── voices/                   # Your voice library (see "Library layout" above)
```

## Troubleshooting

**First run appears stuck for a minute.** Normal. `VoxCPM.from_pretrained()` is downloading the model (~2 GB) from HuggingFace. Progress is on stderr. Subsequent runs skip this.

**Voice sounds generic / nothing like the description.** Description is too abstract. Rewrite with concrete traits (age band, gender, timbre, accent). Re-roll.

**Sentences run together.** Voice design produced <200 ms gaps that didn't qualify for padding. Add `[breath]` or `[quick_breath]` between sentences via `--lines`, or lower `--min-gap-ms` in `generate_voice.py`.

**`torch` / MPS error on Apple Silicon.** The script sets `PYTORCH_ENABLE_MPS_FALLBACK=1`. If that's not enough, edit `generate_voice.py` to force CPU before `from_pretrained()`: `import torch; torch.set_default_device("cpu")`.

**Voice drifts between sentences in a single design take.** Shouldn't happen — `generate_voice.py` does one `generate()` per take. Run with `--dry-run` to confirm the prompt composition. If it still drifts, open an issue.

**`speak.py` errors with "no reference.wav yet".** You haven't saved a take for that voice. Run `save_take.py --name <voice> --take <N>` first.

**Voice sounds slightly different across voicelines in the same saved voice.** Ultimate Cloning is near-deterministic but not perfectly so. If it's off, check that `voice.json`'s `lines` field matches what's actually spoken in `reference.wav` — VoxCPM uses that transcript to lock the voice.

## Acknowledgements

- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB — the underlying TTS model.
- Harvard sentences for the default test set (standard TTS comparison corpus).
